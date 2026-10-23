using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Shared checks for our behaviours. Like the vanilla zones, effects on a car only run on the machine
// that owns that car: it simulates the car, and ClientNetworkTransform shows the result to everyone.
internal static class CarLookup
{
    internal static bool TryGetOwnedCar(Collider other, out PlayerNetworking player, out SphereCarController car)
    {
        player = other.GetComponentInParent<PlayerNetworking>();
        car = player ? player.carController : null;
        return player && player.IsOwner && car && car.sphereRigidbody;
    }

    internal static bool TryGetAnyCar(Collider other, out SphereCarController car)
    {
        var player = other.GetComponentInParent<PlayerNetworking>();
        car = player ? player.carController : null;
        return car;
    }

    // Our zones stay quiet while their obstacle is being carried around during placement.
    internal static bool IsPlaced(Obstacle obstacle) => !obstacle || obstacle.state == Obstacle.ObstacleState.Placed;

    // Single-use pieces (mines, grenades) only go off mid-race, so nothing parked or respawning during
    // the draft, placement or scoreboard uses them up before anyone gets to see them.
    internal static bool IsRacing()
    {
        var gm = Game.GameManager.instance;
        return !gm || !gm.networkVariables || gm.networkVariables.state.Value == Game.GameManager.GameState.Racing;
    }
}
