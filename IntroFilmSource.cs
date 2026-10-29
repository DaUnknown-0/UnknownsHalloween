namespace UnknownsHalloween;

/// <summary>
/// Forgotten Fixes' intro film finds this class next to the plugin class and loads the seasonal chapter from the manifest:
/// film.seasonal.json (chapter + the whole-film file with it), its subtitles and film_full.mp4 as release attachments.
/// Without Forgotten Fixes nothing reads it.
/// </summary>
public static class IntroFilmSource
{
    public const string Manifest = "https://raw.githubusercontent.com/DaUnknown-0/UnknownsHalloween-Assets/main/film/manifest.json";
}
