# Builds thunderstore/icon.png (256x256): a comic burst with three of the cards' renders on top.
param([string]$Repo = (Split-Path -Parent $PSScriptRoot))
Add-Type -AssemblyName System.Drawing
function C([string]$hex) { [System.Drawing.ColorTranslator]::FromHtml($hex) }

$size = 256
$bmp = New-Object System.Drawing.Bitmap $size, $size
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = "AntiAlias"
$g.InterpolationMode = "HighQualityBicubic"
$g.Clear((C "#5B22C9"))
$cx, $cy = 128, 120
for ($i = 0; $i -lt 24; $i += 2) {
    $a0 = 2 * [math]::PI * $i / 24; $a1 = 2 * [math]::PI * ($i + 1) / 24
    $pts = [System.Drawing.PointF[]]@(
        (New-Object System.Drawing.PointF $cx, $cy),
        (New-Object System.Drawing.PointF ($cx + [math]::Cos($a0) * 400), ($cy + [math]::Sin($a0) * 400)),
        (New-Object System.Drawing.PointF ($cx + [math]::Cos($a1) * 400), ($cy + [math]::Sin($a1) * 400)))
    $brush = New-Object System.Drawing.SolidBrush (C "#9B5CFF"); $g.FillPolygon($brush, $pts); $brush.Dispose()
}
$path = New-Object System.Drawing.Drawing2D.GraphicsPath
$path.AddEllipse($cx - 120, $cy - 120, 240, 240)
$glowBrush = New-Object System.Drawing.Drawing2D.PathGradientBrush $path
$glowBrush.CenterColor = [System.Drawing.Color]::FromArgb(220, 240, 225, 255)
$glowBrush.SurroundColors = [System.Drawing.Color[]]@([System.Drawing.Color]::FromArgb(0, 240, 225, 255))
$g.FillPath($glowBrush, $path); $glowBrush.Dispose(); $path.Dispose()

$art = Join-Path $Repo "assets\obstacles"
foreach ($item in @(@("RubberDuck", -20, 92, 150), @("JengaTower", 128, 40, 150), @("Toilet", 40, 30, 190))) {
    $img = [System.Drawing.Image]::FromFile((Join-Path $art "$($item[0]).png"))
    $g.DrawImage($img, [int]$item[1], [int]$item[2], [int]$item[3], [int]$item[3])
    $img.Dispose()
}
$g.Dispose()
$out = Join-Path $Repo "thunderstore\icon.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
"wrote $out"
