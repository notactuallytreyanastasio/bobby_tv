defmodule BobTv.Streaming.FFmpegPort do
  @moduledoc """
  Manages FFmpeg processes using Erlang Ports.
  Handles video duration detection, format conversion, and streaming.
  """
  use GenServer
  require Logger

  @ffmpeg_path System.find_executable("ffmpeg") || "/usr/bin/ffmpeg"
  @ffprobe_path System.find_executable("ffprobe") || "/usr/bin/ffprobe"

  # Client API

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @doc """
  Get video duration in seconds using ffprobe
  """
  def get_duration(video_path) do
    GenServer.call(__MODULE__, {:get_duration, video_path}, :timer.seconds(30))
  end

  @doc """
  Get current playback position for a video being read by OBS
  Returns {elapsed_seconds, total_seconds, percentage}
  """
  def get_playback_position(video_path, start_time) do
    with {:ok, duration} <- get_duration(video_path) do
      elapsed = System.monotonic_time(:second) - start_time
      percentage = (elapsed / duration) * 100
      {:ok, {elapsed, duration, percentage}}
    end
  end

  @doc """
  Convert video to streaming-compatible format if needed
  """
  def convert_video(input_path, output_path) do
    GenServer.call(__MODULE__, {:convert_video, input_path, output_path}, :timer.minutes(10))
  end

  @doc """
  Stream video directly via RTMP (fallback to OBS)
  """
  def stream_rtmp(video_path, rtmp_url, stream_key) do
    GenServer.call(__MODULE__, {:stream_rtmp, video_path, rtmp_url, stream_key})
  end

  # Server Callbacks

  @impl true
  def init(_) do
    Logger.info("FFmpeg port manager initialized")
    {:ok, %{ports: %{}}}
  end

  @impl true
  def handle_call({:get_duration, video_path}, _from, state) do
    args = [
      "-v", "error",
      "-show_entries", "format=duration",
      "-of", "json",
      video_path
    ]

    result = run_command(@ffprobe_path, args)

    duration = case result do
      {:ok, output} ->
        case Jason.decode(output) do
          {:ok, %{"format" => %{"duration" => duration_str}}} ->
            {duration, _} = Float.parse(duration_str)
            {:ok, duration}
          _ ->
            {:error, :parse_error}
        end
      {:error, reason} ->
        {:error, reason}
    end

    {:reply, duration, state}
  end

  @impl true
  def handle_call({:convert_video, input_path, output_path}, _from, state) do
    # Convert to H.264 with AAC audio for maximum compatibility
    args = [
      "-i", input_path,
      "-c:v", "libx264",
      "-preset", "fast",
      "-crf", "22",
      "-c:a", "aac",
      "-b:a", "128k",
      "-movflags", "+faststart",
      "-y",  # Overwrite output
      output_path
    ]

    result = run_command(@ffmpeg_path, args, :timer.minutes(10))
    {:reply, result, state}
  end

  @impl true
  def handle_call({:stream_rtmp, video_path, rtmp_url, stream_key}, from, state) do
    # Start RTMP streaming in background
    args = [
      "-re",  # Read input at native frame rate
      "-i", video_path,
      "-c:v", "libx264",
      "-preset", "veryfast",
      "-maxrate", "3000k",
      "-bufsize", "6000k",
      "-pix_fmt", "yuv420p",
      "-g", "50",
      "-c:a", "aac",
      "-b:a", "128k",
      "-ar", "44100",
      "-f", "flv",
      "#{rtmp_url}/#{stream_key}"
    ]

    port = Port.open({:spawn_executable, @ffmpeg_path}, [
      :binary,
      :exit_status,
      {:args, args},
      {:line, 1024}
    ])

    # Store port reference
    new_state = put_in(state, [:ports, port], %{from: from, type: :rtmp_stream})

    {:noreply, new_state}
  end

  @impl true
  def handle_info({port, {:data, data}}, state) when is_port(port) do
    # Log FFmpeg output for debugging
    Logger.debug("FFmpeg output: #{inspect(data)}")
    {:noreply, state}
  end

  @impl true
  def handle_info({port, {:exit_status, status}}, state) when is_port(port) do
    # Handle port exit
    case get_in(state, [:ports, port]) do
      %{from: from, type: type} ->
        GenServer.reply(from, {:ok, status})
        Logger.info("FFmpeg #{type} process exited with status: #{status}")
        new_state = update_in(state, [:ports], &Map.delete(&1, port))
        {:noreply, new_state}

      nil ->
        {:noreply, state}
    end
  end

  # Private functions

  defp run_command(executable, args, timeout \\ 5000) do
    port = Port.open({:spawn_executable, executable}, [
      :binary,
      :exit_status,
      {:args, args},
      :use_stdio
    ])

    receive do
      {^port, {:exit_status, 0}} ->
        collect_output(port, "")

      {^port, {:exit_status, status}} ->
        Logger.error("Command failed with status #{status}: #{executable} #{Enum.join(args, " ")}")
        {:error, {:exit_status, status}}
    after
      timeout ->
        Port.close(port)
        {:error, :timeout}
    end
  end

  defp collect_output(port, acc) do
    receive do
      {^port, {:data, data}} ->
        collect_output(port, acc <> data)
    after
      100 ->
        {:ok, acc}
    end
  end
end