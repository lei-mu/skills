Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$ConfigPath = "clawhub/skills.publish.json",
    [string]$SkillSlug = "",
    [string]$ExpectedVersion = "",
    [switch]$JsonOutput
)

function Read-Utf8Text {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "文件不存在: $Path"
    }

    $fileBytes = [System.IO.File]::ReadAllBytes($Path)
    if ($fileBytes.Length -ge 3 -and $fileBytes[0] -eq 0xEF -and $fileBytes[1] -eq 0xBB -and $fileBytes[2] -eq 0xBF) {
        throw "文件不能使用 UTF-8 BOM 编码: $Path"
    }

    $utf8Encoding = [System.Text.UTF8Encoding]::new($false, $true)
    try {
        $content = $utf8Encoding.GetString($fileBytes)
    }
    catch {
        throw "文件不是合法的 UTF-8 编码: $Path"
    }

    if ($content.Contains([char]0xFFFD)) {
        throw "文件中检测到乱码替换字符 '�': $Path"
    }

    return $content
}

function Get-FrontMatterValue {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Lines,
        [Parameter(Mandatory = $true)]
        [string]$Key
    )

    foreach ($line in $Lines) {
        if ($line -match "^\s*$([regex]::Escape($Key))\s*:\s*(.+?)\s*$") {
            return $Matches[1].Trim()
        }
    }

    return $null
}

function Get-FrontMatterListValue {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Lines,
        [Parameter(Mandatory = $true)]
        [string]$Key
    )

    $rawValue = Get-FrontMatterValue -Lines $Lines -Key $Key
    if ([string]::IsNullOrWhiteSpace($rawValue)) {
        return @()
    }

    if ($rawValue -notmatch "^\[(.*)\]$") {
        return @()
    }

    $listContent = $Matches[1].Trim()
    if ([string]::IsNullOrWhiteSpace($listContent)) {
        return @()
    }

    return @(
        $listContent.Split(",") |
        ForEach-Object { $_.Trim() } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { $_.Trim("'").Trim('"') }
    )
}

function Get-SkillMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SkillDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Slug
    )

    $skillFilePath = Join-Path $SkillDirectory "SKILL.md"
    $skillContent = Read-Utf8Text -Path $skillFilePath
    $skillLines = [System.Text.RegularExpressions.Regex]::Split($skillContent, "\r?\n")

    if ($skillLines.Count -lt 3 -or $skillLines[0].Trim() -ne "---") {
        throw "SKILL.md 缺少 frontmatter: $skillFilePath"
    }

    $frontMatterEnd = -1
    for ($index = 1; $index -lt $skillLines.Count; $index++) {
        if ($skillLines[$index].Trim() -eq "---") {
            $frontMatterEnd = $index
            break
        }
    }

    if ($frontMatterEnd -lt 0) {
        throw "SKILL.md frontmatter 未正确结束: $skillFilePath"
    }

    $frontMatterLines = if ($frontMatterEnd -gt 1) {
        $skillLines[1..($frontMatterEnd - 1)]
    }
    else {
        @()
    }

    $name = Get-FrontMatterValue -Lines $frontMatterLines -Key "name"
    $version = Get-FrontMatterValue -Lines $frontMatterLines -Key "version"
    $description = Get-FrontMatterValue -Lines $frontMatterLines -Key "description"
    $tags = Get-FrontMatterListValue -Lines $frontMatterLines -Key "tags"

    if ([string]::IsNullOrWhiteSpace($name)) {
        throw "SKILL.md frontmatter 缺少 name: $skillFilePath"
    }
    if ([string]::IsNullOrWhiteSpace($version)) {
        throw "SKILL.md frontmatter 缺少 version: $skillFilePath"
    }
    if ([string]::IsNullOrWhiteSpace($description)) {
        throw "SKILL.md frontmatter 缺少 description: $skillFilePath"
    }
    if ($version -notmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z\.-]+)?(?:\+[0-9A-Za-z\.-]+)?$') {
        throw "SKILL.md version 不是合法的 semver 风格版本: $skillFilePath => $version"
    }
    if ($skillContent.Contains("�")) {
        throw "SKILL.md 中检测到乱码字符 '�': $skillFilePath"
    }

    return [PSCustomObject]@{
        slug        = $Slug
        source      = $SkillDirectory.Replace("\", "/")
        skillFile   = $skillFilePath.Replace("\", "/")
        name        = $name
        version     = $version
        description = $description
        tags        = @($tags)
    }
}

$configContent = Read-Utf8Text -Path $ConfigPath
$config = $configContent | ConvertFrom-Json -Depth 10

if ($null -eq $config.skills -or $config.skills.Count -eq 0) {
    throw "发布配置中未定义任何 skills: $ConfigPath"
}

$skillItems = @()
foreach ($item in $config.skills) {
    if ($null -eq $item) {
        continue
    }

    $isPublishEnabled = $true
    if ($null -ne $item.publish) {
        $isPublishEnabled = [bool]$item.publish
    }
    if (-not $isPublishEnabled) {
        continue
    }

    if ([string]::IsNullOrWhiteSpace($item.source)) {
        throw "发布配置项缺少 source: $ConfigPath"
    }

    $skillDirectory = $item.source
    if (-not (Test-Path -LiteralPath $skillDirectory -PathType Container)) {
        throw "Skill 目录不存在: $skillDirectory"
    }

    $slug = if (-not [string]::IsNullOrWhiteSpace($item.slug)) {
        [string]$item.slug
    }
    else {
        Split-Path -Path $skillDirectory -Leaf
    }

    $skillMetadata = Get-SkillMetadata -SkillDirectory $skillDirectory -Slug $slug
    $skillItems += $skillMetadata
}

if (-not [string]::IsNullOrWhiteSpace($SkillSlug)) {
    $skillItems = @($skillItems | Where-Object { $_.slug -eq $SkillSlug })
    if ($skillItems.Count -eq 0) {
        throw "未在发布配置中找到指定 skill: $SkillSlug"
    }
}

if (-not [string]::IsNullOrWhiteSpace($ExpectedVersion)) {
    foreach ($skillItem in $skillItems) {
        if ($skillItem.version -ne $ExpectedVersion) {
            throw "版本不一致: slug=$($skillItem.slug), SKILL.md=$($skillItem.version), 期望版本=$ExpectedVersion"
        }
    }
}

$result = [PSCustomObject]@{
    generatedAt = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    count       = $skillItems.Count
    skills      = @($skillItems)
}

if ($env:GITHUB_OUTPUT) {
    $compressedJson = $result | ConvertTo-Json -Depth 10 -Compress
    "count=$($result.count)" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
    "has_skills=$([string]($result.count -gt 0).ToLowerInvariant())" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
    "skills_json<<EOF" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
    $compressedJson | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
    "EOF" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
}

if ($JsonOutput) {
    $result | ConvertTo-Json -Depth 10
}
else {
    $skillItems | Format-Table slug, name, version, source -AutoSize
}
