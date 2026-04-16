Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$ConfigPath = "clawhub/skills.publish.json",
    [string]$SkillSlug,
    [string]$ExpectedVersion,
    [string]$Changelog = ""
)

if ([string]::IsNullOrWhiteSpace($env:CLAWHUB_TOKEN)) {
    throw "缺少环境变量 CLAWHUB_TOKEN，无法执行 ClawHub 发布。"
}

$getSkillsScriptPath = Join-Path $PSScriptRoot "Get-ClawHubSkills.ps1"
$resolvedSkillsJson = & $getSkillsScriptPath -ConfigPath $ConfigPath -SkillSlug $SkillSlug -ExpectedVersion $ExpectedVersion -JsonOutput
$resolvedSkills = $resolvedSkillsJson | ConvertFrom-Json -Depth 10

if ($null -eq $resolvedSkills.skills -or $resolvedSkills.skills.Count -eq 0) {
    throw "没有可发布的 skill。"
}

Write-Host "开始登录 ClawHub CLI..."
& npx --yes clawhub@latest login --token $env:CLAWHUB_TOKEN --no-browser
if ($LASTEXITCODE -ne 0) {
    throw "ClawHub CLI 登录失败。"
}

$publishResults = New-Object System.Collections.Generic.List[object]

foreach ($skill in $resolvedSkills.skills) {
    $slug = [string]$skill.slug
    $version = [string]$skill.version
    $source = [string]$skill.source
    $name = [string]$skill.name

    Write-Host "检查远端版本是否已存在: slug=$slug version=$version"
    $inspectOutput = & npx --yes clawhub@latest inspect --version $version $slug 2>&1 | Out-String
    $inspectExitCode = $LASTEXITCODE
    $alreadyPublished = $inspectExitCode -eq 0 -and $inspectOutput -match [regex]::Escape($version)

    if ($alreadyPublished) {
        Write-Host "检测到远端已存在相同版本，跳过发布: slug=$slug version=$version"
        $publishResults.Add([PSCustomObject]@{
                slug    = $slug
                version = $version
                status  = "skipped"
                reason  = "version_exists"
            })
        continue
    }

    $publishArguments = @(
        "--yes",
        "clawhub@latest",
        "skill",
        "publish",
        $source,
        "--slug",
        $slug,
        "--name",
        $name,
        "--version",
        $version
    )

    if (-not [string]::IsNullOrWhiteSpace($Changelog)) {
        $publishArguments += @("--changelog", $Changelog)
    }

    Write-Host "执行发布: slug=$slug version=$version source=$source"
    & npx @publishArguments
    $publishExitCode = $LASTEXITCODE

    if ($publishExitCode -eq 0) {
        $publishResults.Add([PSCustomObject]@{
                slug    = $slug
                version = $version
                status  = "published"
                reason  = ""
            })
        continue
    }

    Write-Warning "发布失败，继续处理下一个 skill: slug=$slug version=$version"
    $publishResults.Add([PSCustomObject]@{
            slug    = $slug
            version = $version
            status  = "failed"
            reason  = "publish_command_failed"
        })
}

Write-Host "发布结果汇总:"
$publishResults | Format-Table slug, version, status, reason -AutoSize

$failedItems = @($publishResults | Where-Object { $_.status -eq "failed" })
if ($failedItems.Count -gt 0) {
    throw "存在发布失败的 skill，请检查上面的日志。"
}
