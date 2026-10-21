using System;
using System.IO;
using Newtonsoft.Json;
using Obstacles;

namespace SlipSkid.CustomContent;

// An obstacle whose look, colliders, zones and animation come from obstacles/<Id>.json,
// exported from Blender by tools/blender/ss_export.py. Its card art is obstacles/<Id>.png.
internal sealed class DataObstacle : CustomObstacle
{
    private static readonly string Folder = Path.Combine(Path.GetDirectoryName(typeof(Plugin).Assembly.Location), "obstacles");

    private readonly string _id;
    private readonly ObstacleData _data;

    public DataObstacle(string id, string guid)
    {
        _id = id;
        Guid = new Guid(guid);
        _data = Load(id);
    }

    public override string Id => _id;
    public override Guid Guid { get; }
    public override string DisplayName => _data?.name ?? _id;
    public override string Description => _data?.description ?? "<color=#E0204A>Missing data file.</color>";
    public override string ThumbnailFile => Path.Combine("obstacles", $"{_id}.png");
    public override string FullArtFile => _data is { fullArt: true } ? Path.Combine("obstacles", $"{_id}_card.png") : null;
    public override string PartnerId => _data?.partner;
    public override bool IsPartnerOnly => _data is { partnerOnly: true };
    public override string DefaultCarrier => _data?.carrier;
    public override bool KeepCarrier => _data is { keepCarrier: true };

    protected override CardRarity DefaultRarity =>
        _data != null && Enum.TryParse(_data.rarity, true, out CardRarity rarity) ? rarity : CardRarity.Common;

    internal override void Build(Obstacle obstacle, CarrierParts carrier)
    {
        // A missing file still registers the card (so catalog indices match every machine), it just builds nothing.
        if (_data == null)
            return;

        // Scatter card: the vanilla scatter (e.g. LandMineScatter) drops our obstacle instead of its own.
        // Only the host spawns the pieces, but setting it everywhere keeps the scatter's log line right.
        if (!string.IsNullOrEmpty(_data.scatter) && obstacle is ObstacleScatter scatter)
        {
            var piece = CardRegistry.DescriptionOf(_data.scatter);
            if (piece)
                scatter.obstacleToScatter = piece;
            scatter.count = _data.scatterCount;
        }
        // Surface-swap card: swaps road and obstacles to our surface instead of the carrier's.
        if (_data.surface == "reverse" && obstacle is ObstacleSurfaceSwap swap && ReverseSurface.Instance)
            swap.surfaceToSwapTo = ReverseSurface.Instance;

        if (_data.nodes.Count > 0)
            DataObstacleBuilder.Build(_id, _data, obstacle, carrier);
    }

    private static ObstacleData Load(string id)
    {
        string path = Path.Combine(Folder, $"{id}.json");
        try
        {
            if (!File.Exists(path))
            {
                Plugin.Log.LogError($"DataObstacle: {path} not found");
                return null;
            }
            var data = JsonConvert.DeserializeObject<ObstacleData>(File.ReadAllText(path));
            Plugin.Log.LogInfo($"DataObstacle: loaded {id} ({data.nodes.Count} nodes)");
            return data;
        }
        catch (Exception e)
        {
            Plugin.Log.LogError($"DataObstacle: couldn't read {path}: {e.Message}");
            return null;
        }
    }
}
