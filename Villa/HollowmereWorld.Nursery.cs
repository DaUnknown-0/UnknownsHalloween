using System;
using Hazel;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    private const byte SubTapeRequest = 44, SubTapePlay = 45, SubTapeRound = 46;
    private const float TapeCooldown = 30f;
    private const float TapeReach = 1.10f;
    private static AudioClip _tapeEnglish, _tapeGerman;
    private Vector2? _tapeSpot;
    private uint _tapeRound;
    private bool _tapeUsed, _tapeWasMeeting;
    private float _tapeReadyAt;
    private AudioSource _tapeAudio;
    private float _diagTapeDeadline;

    private static bool TapeMeeting => MeetingHud.Instance != null || ExileController.Instance != null;

    private void TapeBuild()
    {
        var props = AtlasMaps.Props("nursery_tonband");
        _tapeSpot = props.Count == 0 ? null : props[0].Pos + new Vector2(0f, 0.44f);
        _tapeRound = 0;
        _tapeUsed = _tapeWasMeeting = false;
        _tapeReadyAt = 0f;
    }

    private void TapeTick()
    {
        if (!_tapeSpot.HasValue) return;
        bool meeting = TapeMeeting;
        if (!meeting && _tapeWasMeeting && AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost)
        {
            ApplyTapeRound(_tapeRound + 1);
            SendRitual(SubTapeRound, writer => writer.Write(_tapeRound));
        }
        _tapeWasMeeting = meeting;
    }

    private void ApplyTapeRound(uint round)
    {
        _tapeRound = round;
        _tapeUsed = false;
    }

    private bool TapeReady => !_tapeUsed && !TapeMeeting && Time.realtimeSinceStartup >= _tapeReadyAt;

    private bool OfferTape()
    {
        if (!_tapeSpot.HasValue || TapeMeeting || !AtlasMaps.CanReach(_tapeSpot.Value, TapeReach)
            || !TapeInReach(PlayerControl.LocalPlayer)) return false;
        bool german = HwMechanics.De();
        var seconds = Mathf.CeilToInt(_tapeReadyAt - Time.realtimeSinceStartup);
        string label = _tapeUsed ? (german ? "NACH MEETING" : "AFTER MEETING")
            : seconds > 0 ? (german ? $"WARTEN {seconds}" : $"WAIT {seconds}")
            : (german ? "ABSPIELEN" : "PLAY TAPE");
        AtlasMaps.OfferUse(label, "task_villa_btn_secret.png", RequestTape, enabled: TapeReady);
        return true;
    }

    private bool TapeInReach(PlayerControl player)
    {
        if (!_tapeSpot.HasValue || player == null || player.Data == null || player.Data.Disconnected
            || player.Data.IsDead || player.inVent) return false;
        Vector2 from = player.GetTruePosition(), to = _tapeSpot.Value;
        return (from - to).sqrMagnitude < TapeReach * TapeReach
            && !PhysicsHelpers.AnythingBetween(from, to, Constants.ShadowMask, false);
    }

    private void RequestTape()
    {
        if (!TapeReady || !TapeInReach(PlayerControl.LocalPlayer)) return;
        if (AmongUsClient.Instance.AmHost) HostPlayTape(PlayerControl.LocalPlayer, _tapeRound);
        else SendRitual(SubTapeRequest, writer => writer.Write(_tapeRound));
    }

    private bool HostPlayTape(PlayerControl player, uint round)
    {
        if (!AmongUsClient.Instance.AmHost || round != _tapeRound || !TapeReady || !TapeInReach(player))
            return false;
        ApplyTapePlay();
        SendRitual(SubTapePlay, writer => writer.Write(round));
        return true;
    }

    private void ApplyTapePlay()
    {
        _tapeUsed = true;
        _tapeReadyAt = Time.realtimeSinceStartup + TapeCooldown;
        _tapeAudio = PlayTapeVoice(HwMechanics.De());
    }

    private static AudioClip TapeClip(bool german)
    {
        ref AudioClip clip = ref (german ? ref _tapeGerman : ref _tapeEnglish);
        if (clip != null) return clip;
        string name = german ? "nursery_tape_de" : "nursery_tape_en";
        using var stream = HalloweenAssets.Open($"UnknownsHalloween.Resources.{name}.ogg");
        return stream == null ? null : clip = OggClip(stream, name);
    }

    private static AudioSource PlayTapeVoice(bool german)
    {
        try
        {
            var clip = TapeClip(german);
            if (clip == null || SoundManager.Instance == null) return null;
            var source = SoundManager.Instance.PlaySound(clip, false, 0.92f);
            if (source != null) source.spatialBlend = 0f;
            return source;
        }
        catch (Exception ex)
        {
            HalloweenPlugin.Logger.LogWarning($"{LogPrefix} nursery tape audio failed: {ex.Message}");
            return null;
        }
    }

    private static bool HandleTapeRpc(byte sub, MessageReader reader)
    {
        if (sub is not (SubTapeRequest or SubTapePlay or SubTapeRound)) return false;
        var world = _current;
        if (world == null || !world._tapeSpot.HasValue) return true;
        if (sub == SubTapeRequest)
        {
            if (AmongUsClient.Instance.AmHost) world.HostPlayTape(UCRpc.Sender, reader.ReadUInt32());
            return true;
        }
        if (!UCRpc.RequireHost("Hollowmere.NurseryTape")) return true;
        uint round = reader.ReadUInt32();
        if (sub == SubTapeRound && round > world._tapeRound) world.ApplyTapeRound(round);
        if (sub == SubTapePlay && round == world._tapeRound && !world._tapeUsed) world.ApplyTapePlay();
        return true;
    }

    private void DiagTape(PlayerControl lp)
    {
        void Next(float delay)
        {
            _diagStep++;
            _diagAt = Time.time + delay;
        }
        void Check(string name, bool pass) =>
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: nursery tape {name} {(pass ? "PASS" : "FAIL")}");
        void Finish()
        {
            _diagTask++;
            _diagStep = 0;
            _diagAt = Time.time + 0.5f;
        }

        switch (_diagStep)
        {
            case 0:
                Check("recorder present", _tapeSpot.HasValue);
                if (!_tapeSpot.HasValue) { Finish(); return; }
                lp.NetTransform.RpcSnapTo(_tapeSpot.Value + new Vector2(2f, 2f));
                Next(0.6f);
                break;
            case 1:
                Check("distant player refused", !HostPlayTape(lp, _tapeRound));
                lp.NetTransform.RpcSnapTo(_tapeSpot.Value + new Vector2(0f, 0.33f));
                Next(0.7f);
                break;
            case 2:
                var button = HudManager.Instance.UseButton;
                Check("use button offered", button.buttonLabelText.text is "PLAY TAPE" or "ABSPIELEN");
                AtlasMaps.Shot("nursery_tape", "use");
                button.GetComponent<PassiveButton>().OnClick.Invoke();
                Check("use button starts tape", _tapeUsed);
                Check("global audio source plays", _tapeAudio != null && _tapeAudio.isPlaying && _tapeAudio.spatialBlend == 0f);
                Check("both Ogg clips decoded", TapeClip(false) != null && TapeClip(true) != null);
                Check("repeat refused", !HostPlayTape(lp, _tapeRound));
                _diagTapeDeadline = _tapeReadyAt;
                Next(2f);
                break;
            case 3:
                lp.CmdReportDeadBody(null);
                Next(4f);
                break;
            case 4:
                var meeting = MeetingHud.Instance;
                Check("meeting opened", meeting != null);
                if (meeting == null) { Finish(); return; }
                Check("meeting blocks requests", !TapeReady);
                Next(4f);
                break;
            case 5:
                var voting = MeetingHud.Instance;
                if (voting != null && voting.state is (MeetingHud.VoteStates.NotVoted or MeetingHud.VoteStates.Voted))
                    voting.RpcVotingComplete(new Il2CppStructArray<MeetingHud.VoterState>(0), null, true);
                else if (voting != null && voting.state is not (MeetingHud.VoteStates.Results or MeetingHud.VoteStates.Proceeding))
                {
                    _diagAt = Time.time + 0.25f;
                    return;
                }
                Next(0.5f);
                break;
            case 6:
                var results = MeetingHud.Instance;
                if (results != null && results.state == MeetingHud.VoteStates.Results)
                {
                    var proceed = results.ProceedButton;
                    if (proceed == null || !proceed.gameObject.activeInHierarchy)
                    {
                        _diagAt = Time.time + 0.25f;
                        return;
                    }
                    proceed.OnClick.Invoke();
                }
                Next(0.5f);
                break;
            case 7:
                if (TapeMeeting) { _diagAt = Time.time + 0.25f; return; }
                Check("meeting resets round", _tapeRound == 1 && !_tapeUsed);
                Check("30-second cooldown survives meeting", _tapeReadyAt == _diagTapeDeadline
                    && TapeReady == (Time.realtimeSinceStartup >= _diagTapeDeadline));
                Next(Mathf.Max(0f, _tapeReadyAt - Time.realtimeSinceStartup) + 0.2f);
                break;
            case 8:
                lp.NetTransform.RpcSnapTo(_tapeSpot.Value + new Vector2(0f, 0.33f));
                Next(0.6f);
                break;
            case 9:
                Check("stale round refused", !HostPlayTape(lp, _tapeRound - 1));
                Check("can play again after meeting and cooldown", HostPlayTape(lp, _tapeRound));
                Next(TapeCooldown + 0.3f);
                break;
            case 10:
                Check("same round stays locked after 30 seconds", Time.realtimeSinceStartup >= _tapeReadyAt
                    && !HostPlayTape(lp, _tapeRound));
                Finish();
                break;
        }
    }
}
