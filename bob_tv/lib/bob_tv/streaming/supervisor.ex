defmodule BobTv.Streaming.Supervisor do
  @moduledoc """
  Supervisor for the streaming system components.
  Manages video downloading, playback coordination, and overlay generation.
  """
  use Supervisor

  def start_link(init_arg) do
    Supervisor.start_link(__MODULE__, init_arg, name: __MODULE__)
  end

  @impl true
  def init(_init_arg) do
    children = [
      # Video state storage
      {BobTv.Streaming.State, []},

      # Video download manager
      {BobTv.Streaming.VideoManager, []},

      # Stream coordination and file swapping
      {BobTv.Streaming.StreamCoordinator, []},

      # HTML overlay generator
      {BobTv.Streaming.OverlayGenerator, []},

      # FFmpeg process manager
      {BobTv.Streaming.FFmpegPort, []}
    ]

    # Restart strategy: one_for_one means if a child crashes, only that child is restarted
    Supervisor.init(children, strategy: :one_for_one)
  end
end