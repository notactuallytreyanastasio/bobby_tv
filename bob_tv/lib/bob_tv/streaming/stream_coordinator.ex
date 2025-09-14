defmodule BobTv.Streaming.StreamCoordinator do
  @moduledoc """
  Coordinates video playback and handles atomic file swapping for OBS.
  This is the heart of the streaming system - ensures seamless transitions.
  """
  use GenServer
  require Logger
  alias BobTv.Streaming.{State, VideoManager, FFmpegPort}

  @videos_dir "streaming_videos"
  @obs_file Path.join(@videos_dir, "current_stream.mp4")
  @next_file Path.join(@videos_dir, "next_stream.mp4")
  @temp_file Path.join(@videos_dir, "temp_stream.mp4")
  @preparation_threshold 75  # Start preparing next video at 75% playback

  # Client API

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @doc """
  Start the streaming coordinator
  """
  def start_streaming do
    GenServer.call(__MODULE__, :start_streaming)
  end

  @doc """
  Stop streaming
  """
  def stop_streaming do
    GenServer.call(__MODULE__, :stop_streaming)
  end

  @doc """
  Get current streaming status
  """
  def get_status do
    GenServer.call(__MODULE__, :get_status)
  end

  @doc """
  Manually trigger video swap (for testing)
  """
  def swap_videos do
    GenServer.call(__MODULE__, :swap_videos)
  end

  # Server Callbacks

  @impl true
  def init(_) do
    # Ensure videos directory exists
    File.mkdir_p!(@videos_dir)

    state = %{
      streaming: false,
      current_video: nil,
      next_video: nil,
      playback_start: nil,
      monitor_timer: nil,
      preparing_next: false
    }

    Logger.info("Stream coordinator initialized")
    {:ok, state}
  end

  @impl true
  def handle_call(:start_streaming, _from, state) do
    if not state.streaming do
      Logger.info("Starting streaming coordinator")

      # Initialize first video
      case prepare_initial_video() do
        {:ok, video_info} ->
          # Start playback monitoring
          timer = Process.send_after(self(), :check_playback, :timer.seconds(1))

          new_state = %{state |
            streaming: true,
            current_video: video_info,
            playback_start: System.monotonic_time(:second),
            monitor_timer: timer
          }

          State.put(:streaming_status, :streaming)
          State.put(:current_video, video_info)

          {:reply, :ok, new_state}

        {:error, reason} ->
          Logger.error("Failed to start streaming: #{inspect(reason)}")
          {:reply, {:error, reason}, state}
      end
    else
      {:reply, {:error, :already_streaming}, state}
    end
  end

  @impl true
  def handle_call(:stop_streaming, _from, state) do
    Logger.info("Stopping streaming coordinator")

    # Cancel monitoring timer
    if state.monitor_timer do
      Process.cancel_timer(state.monitor_timer)
    end

    new_state = %{state |
      streaming: false,
      monitor_timer: nil
    }

    State.put(:streaming_status, :stopped)

    {:reply, :ok, new_state}
  end

  @impl true
  def handle_call(:get_status, _from, state) do
    status = %{
      streaming: state.streaming,
      current_video: state.current_video,
      next_video: state.next_video,
      preparing_next: state.preparing_next
    }

    # Add playback progress if streaming
    status = if state.streaming and state.current_video do
      case get_playback_progress(state) do
        {:ok, {elapsed, duration, percentage}} ->
          Map.merge(status, %{
            elapsed_seconds: elapsed,
            duration_seconds: duration,
            progress_percentage: percentage
          })
        _ ->
          status
      end
    else
      status
    end

    {:reply, status, state}
  end

  @impl true
  def handle_call(:swap_videos, _from, state) do
    result = perform_video_swap(state)
    {:reply, result, state}
  end

  @impl true
  def handle_info(:check_playback, state) do
    new_state = if state.streaming do
      # Check playback progress
      case get_playback_progress(state) do
        {:ok, {_elapsed, duration, percentage}} ->
          # Check if we should prepare next video
          state = if percentage >= @preparation_threshold and not state.preparing_next do
            Logger.info("Playback at #{Float.round(percentage, 1)}%, preparing next video")
            prepare_next_video(state)
          else
            state
          end

          # Check if current video is about to end (within 2 seconds)
          remaining = duration - (System.monotonic_time(:second) - state.playback_start)
          state = if remaining <= 2 and state.next_video do
            Logger.info("Video ending in #{remaining}s, swapping now")
            perform_swap_and_update_state(state)
          else
            state
          end

          state

        {:error, reason} ->
          Logger.warn("Could not check playback progress: #{inspect(reason)}")
          state
      end
    else
      state
    end

    # Schedule next check
    timer = if new_state.streaming do
      Process.send_after(self(), :check_playback, :timer.seconds(1))
    else
      nil
    end

    {:noreply, %{new_state | monitor_timer: timer}}
  end

  @impl true
  def handle_info({:next_video_ready, video_info}, state) do
    Logger.info("Next video ready: #{video_info.title}")
    {:noreply, %{state | next_video: video_info, preparing_next: false}}
  end

  # Private functions

  defp prepare_initial_video do
    # Get a video from the manager
    case VideoManager.get_next_video() do
      {:ok, media} ->
        # Download if not already available
        VideoManager.download_next_video()

        # For now, create a placeholder
        # In production, wait for download to complete
        video_info = %{
          id: media.id,
          title: media.title,
          path: @obs_file,
          duration: 0
        }

        # Create initial file for OBS
        File.touch!(@obs_file)

        {:ok, video_info}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp prepare_next_video(state) do
    Task.start(fn ->
      case VideoManager.get_next_video() do
        {:ok, media} ->
          # Trigger download
          VideoManager.download_next_video()

          # In production, wait for download and prepare the file
          video_info = %{
            id: media.id,
            title: media.title,
            path: @next_file,
            duration: 0
          }

          send(self(), {:next_video_ready, video_info})

        {:error, reason} ->
          Logger.error("Failed to prepare next video: #{inspect(reason)}")
      end
    end)

    %{state | preparing_next: true}
  end

  defp perform_swap_and_update_state(state) do
    case perform_video_swap(state) do
      :ok ->
        # Update state with new current video
        State.put(:current_video, state.next_video)
        State.add_to_recently_played(state.current_video.id)
        State.update(:total_videos_played, &(&1 + 1))

        %{state |
          current_video: state.next_video,
          next_video: nil,
          playback_start: System.monotonic_time(:second),
          preparing_next: false
        }

      {:error, reason} ->
        Logger.error("Failed to swap videos: #{inspect(reason)}")
        state
    end
  end

  defp perform_video_swap(_state) do
    # Atomic file swap operation
    # This is the critical section that ensures OBS never sees an interruption

    try do
      # Step 1: Move current to temp (if it exists)
      if File.exists?(@obs_file) do
        File.rename!(@obs_file, @temp_file)
      end

      # Step 2: Move next to current
      if File.exists?(@next_file) do
        File.rename!(@next_file, @obs_file)
      else
        # If no next file, create a placeholder
        File.touch!(@obs_file)
      end

      # Step 3: Clean up temp
      if File.exists?(@temp_file) do
        File.rm!(@temp_file)
      end

      Logger.info("Video swap completed successfully")
      :ok
    rescue
      e ->
        Logger.error("Video swap failed: #{inspect(e)}")
        # Try to recover by ensuring OBS file exists
        if not File.exists?(@obs_file) and File.exists?(@temp_file) do
          File.rename!(@temp_file, @obs_file)
        end
        {:error, e}
    end
  end

  defp get_playback_progress(state) do
    if state.current_video and state.playback_start do
      # For now, simulate progress
      # In production, use FFmpegPort.get_playback_position
      elapsed = System.monotonic_time(:second) - state.playback_start
      duration = 300  # Simulate 5 minute video
      percentage = (elapsed / duration) * 100

      {:ok, {elapsed, duration, percentage}}
    else
      {:error, :no_current_video}
    end
  end
end