# Unknown's Halloween

Add-on for [Unknown's Collection](https://github.com/DaUnknown-0/UnknownsCollection) (The Other Roles, Among Us).

## Contents

- **Four full-body costume hats:** Halloween Freddy, Halloween Jason, Halloween Xenomorph, Halloween Ghostface.
  Each has a 16-frame idle loop, a 12-frame walk loop synced to the crewmate's run cycle, a back layer and a ladder pose.
- **Kill cutscenes:** a frame-by-frame scene per costume. It plays only when the killer wears the costume
  (current outfit, so camouflage or morph hides it) on a normal field kill. Sound is the vanilla kill stinger.
- **Xenomorph role (Neutral, killer):** looks like a Crewmate, transforms on a button (F) for a set time,
  then kills (Q), moves faster, sees like an Impostor and may vent. Wins like the Jackal, alone.
  Options 1785-1792 in the Neutral tab, including "Jackal And Xenomorph Exclude Each Other".
  While the role is enabled, the Xenomorph costume cannot be worn as an ordinary hat.

## Requirements

- Among Us 2024.11.26, BepInEx 6.0.0-be.697, Reactor 2.3.1
- The Other Roles
- Unknown's Collection (hard dependency: RPC channel, options, role draft, guesser)

Put `UnknownsHalloween.dll` into `BepInEx/plugins` next to `UnknownsCollection.dll`.

## Releases

Pushing a tag `vX.Y.Z` (stable) or `vX.Y.Z.W` (test version) builds the DLL in GitHub Actions and attaches it to a release.

## License

GPL-3.0-or-later, see [LICENSE](LICENSE). Based on The Other Roles (GPL-3.0).
