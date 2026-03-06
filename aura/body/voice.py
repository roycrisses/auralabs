"""Voice tools — text-to-speech and speech-to-text using Windows SAPI.

Uses the built-in Windows COM speech API (no external dependencies).
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from aura.body.registry import register_tool


@register_tool("speak")
def speak(text: str, rate: int = 0) -> str:
    """Convert text to speech using Windows SAPI.

    Args:
        text: Text to speak aloud.
        rate: Speech rate adjustment (-5 to 5, 0 is normal).
    """
    rate = max(-5, min(5, rate))
    # Escape for PowerShell
    escaped = text.replace('"', '`"').replace("'", "''").replace("\n", " ")

    ps_script = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = {rate}
    $synth.Speak("{escaped}")
    $synth.Dispose()
    """

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return f"Spoke: {text[:80]}..."
        return f"TTS error: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return "TTS timed out"
    except Exception as e:
        return f"TTS failed: {e}"


@register_tool("speak_to_file")
def speak_to_file(text: str, output_path: str = "", rate: int = 0) -> str:
    """Convert text to a WAV audio file using Windows SAPI.

    Args:
        text: Text to convert to speech.
        output_path: Path for the output WAV file. Auto-generated if empty.
        rate: Speech rate (-5 to 5).
    """
    rate = max(-5, min(5, rate))

    if not output_path:
        cache_dir = Path(r"D:\automation\aura\.cache\audio")
        cache_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(cache_dir / f"speech_{ts}.wav")

    escaped = text.replace('"', '`"').replace("'", "''").replace("\n", " ")
    out_escaped = output_path.replace("\\", "\\\\")

    ps_script = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = {rate}
    $synth.SetOutputToWaveFile("{out_escaped}")
    $synth.Speak("{escaped}")
    $synth.Dispose()
    """

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and Path(output_path).exists():
            return f"Audio saved: {output_path}"
        return f"TTS-to-file error: {result.stderr[:200]}"
    except Exception as e:
        return f"TTS-to-file failed: {e}"


@register_tool("listen")
def listen(duration: int = 5) -> str:
    """Listen to microphone input and transcribe using Windows speech recognition.

    Args:
        duration: Maximum listening duration in seconds (1-30).
    """
    duration = max(1, min(30, duration))

    ps_script = f"""
    Add-Type -AssemblyName System.Speech
    $recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $recognizer.SetInputToDefaultAudioDevice()

    # Load default grammar
    $grammar = New-Object System.Speech.Recognition.DictationGrammar
    $recognizer.LoadGrammar($grammar)

    $recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds({duration})
    $recognizer.BabbleTimeout = [TimeSpan]::FromSeconds({duration})

    try {{
        $result = $recognizer.Recognize([TimeSpan]::FromSeconds({duration}))
        if ($result) {{
            Write-Output $result.Text
        }} else {{
            Write-Output "(no speech detected)"
        }}
    }} catch {{
        Write-Output "(speech recognition error: $($_.Exception.Message))"
    }} finally {{
        $recognizer.Dispose()
    }}
    """

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=duration + 10,
        )
        output = result.stdout.strip()
        if output:
            return output
        if result.stderr:
            return f"(listen error: {result.stderr[:200]})"
        return "(no speech detected)"
    except subprocess.TimeoutExpired:
        return "(listening timed out)"
    except Exception as e:
        return f"(listen failed: {e})"
