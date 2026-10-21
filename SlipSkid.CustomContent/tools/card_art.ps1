# Composites a full-art ("epic") card: comic burst background + a transparent Blender render on top.
# Usage: .\card_art.ps1 -Foreground renders\Toilet_card_fg.png -Out ..\assets\obstacles\Toilet_card.png
# The game draws the card name at the bottom and the description over the lower middle, so the art
# keeps its subject in the upper 60% and darkens the bottom for legibility.
param(
    [Parameter(Mandatory)] [string]$Foreground,
    [Parameter(Mandatory)] [string]$Out,
    [string]$RayA = "#3D8BFF",
    [string]$RayB = "#1F5FE0",
    [string]$Glow = "#BFF0FF"
)
Add-Type -AssemblyName System.Drawing
function C([string]$hex, [int]$alpha = 255) {
    $c = [System.Drawing.ColorTranslator]::FromHtml($hex)
    [System.Drawing.Color]::FromArgb($alpha, $c.R, $c.G, $c.B)
}

$w, $h = 720, 1024
$cx, $cy = 360, 430
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = "AntiAlias"
$g.InterpolationMode = "HighQualityBicubic"
$g.Clear((C $RayB))

# Burst: alternating wedges around the subject.
$rays = 28
for ($i = 0; $i -lt $rays; $i += 2) {
    $a0 = 2 * [math]::PI * $i / $rays
    $a1 = 2 * [math]::PI * ($i + 1) / $rays
    $pts = [System.Drawing.PointF[]]@(
        (New-Object System.Drawing.PointF $cx, $cy),
        (New-Object System.Drawing.PointF ($cx + [math]::Cos($a0) * 2000), ($cy + [math]::Sin($a0) * 2000)),
        (New-Object System.Drawing.PointF ($cx + [math]::Cos($a1) * 2000), ($cy + [math]::Sin($a1) * 2000)))
    $brush = New-Object System.Drawing.SolidBrush (C $RayA)
    $g.FillPolygon($brush, $pts)
    $brush.Dispose()
}

# Halftone dots, denser towards the edges.
$dot = New-Object System.Drawing.SolidBrush (C "#FFFFFF" 46)
for ($y = 0; $y -lt $h; $y += 22) {
    for ($x = (($y / 22) % 2) * 11; $x -lt $w; $x += 22) {
        $d = [math]::Sqrt(($x - $cx) * ($x - $cx) + ($y - $cy) * ($y - $cy))
        $r = [math]::Min(7.0, [math]::Max(0.0, ($d - 180) / 60))
        if ($r -gt 0.5) { $g.FillEllipse($dot, $x - $r, $y - $r, 2 * $r, 2 * $r) }
    }
}
$dot.Dispose()

# Soft glow behind the subject.
# (PowerShell names are case-insensitive, so the brush can't be called $glow next to the $Glow parameter.)
$path = New-Object System.Drawing.Drawing2D.GraphicsPath
$path.AddEllipse($cx - 330, $cy - 330, 660, 660)
$glowBrush = New-Object System.Drawing.Drawing2D.PathGradientBrush $path
$glowBrush.CenterColor = (C $Glow 235)
$glowBrush.SurroundColors = [System.Drawing.Color[]]@((C $Glow 0))
$g.FillPath($glowBrush, $path)
$glowBrush.Dispose(); $path.Dispose()

# The render, lifted so the subject sits in the top part of the card, centred on the burst.
$fg = [System.Drawing.Image]::FromFile((Resolve-Path $Foreground))
$g.DrawImage($fg, 0, $cy - $h / 2, $w, $h)
$fg.Dispose()

# Darken the bottom so the game's text stays readable.
$rect = New-Object System.Drawing.Rectangle 0, 560, $w, ($h - 560)
$shade = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, (C "#06123A" 0), (C "#06123A" 190), 90.0
$g.FillRectangle($shade, $rect)
$shade.Dispose()

$g.Dispose()
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
"wrote $Out"
