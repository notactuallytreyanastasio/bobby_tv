defmodule BobTv.Streaming.OverlayGenerator do
  @moduledoc """
  Generates HTML overlays for the stream (current video info, upcoming videos, etc.)
  Serves these overlays via a simple web server for OBS Browser Source.
  """
  use GenServer
  require Logger
  alias BobTv.Streaming.State
  alias BobTv.Catalog

  @overlay_dir "priv/static/overlays"
  @current_file Path.join(@overlay_dir, "current.html")
  @next_file Path.join(@overlay_dir, "next.html")
  @schedule_file Path.join(@overlay_dir, "schedule.html")
  @update_interval :timer.seconds(5)

  # Client API

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @doc """
  Manually trigger overlay update
  """
  def update_overlays do
    GenServer.cast(__MODULE__, :update_overlays)
  end

  @doc """
  Get current overlay status
  """
  def get_status do
    GenServer.call(__MODULE__, :get_status)
  end

  # Server Callbacks

  @impl true
  def init(_) do
    # Ensure overlay directory exists
    File.mkdir_p!(@overlay_dir)
    
    # Generate initial overlays
    generate_all_overlays()
    
    # Schedule periodic updates
    timer = Process.send_after(self(), :update_overlays, @update_interval)
    
    state = %{
      last_update: System.monotonic_time(:second),
      update_timer: timer,
      active: true
    }
    
    Logger.info("Overlay generator initialized")
    {:ok, state}
  end

  @impl true
  def handle_cast(:update_overlays, state) do
    generate_all_overlays()
    {:noreply, %{state | last_update: System.monotonic_time(:second)}}
  end

  @impl true
  def handle_call(:get_status, _from, state) do
    status = %{
      active: state.active,
      last_update: state.last_update,
      overlay_files: [
        @current_file,
        @next_file,
        @schedule_file
      ]
    }
    {:reply, status, state}
  end

  @impl true
  def handle_info(:update_overlays, state) do
    if state.active do
      generate_all_overlays()
    end
    
    # Schedule next update
    timer = Process.send_after(self(), :update_overlays, @update_interval)
    
    {:noreply, %{state | update_timer: timer, last_update: System.monotonic_time(:second)}}
  end

  # Private functions

  defp generate_all_overlays do
    generate_current_overlay()
    generate_next_overlay()
    generate_schedule_overlay()
  end

  defp generate_current_overlay do
    content = case State.get(:current_video) do
      {:ok, video} when not is_nil(video) ->
        build_current_html(video)
      _ ->
        build_empty_current_html()
    end
    
    File.write!(@current_file, content)
  end

  defp generate_next_overlay do
    content = case State.get(:next_video) do
      {:ok, video} when not is_nil(video) ->
        build_next_html(video)
      _ ->
        build_empty_next_html()
    end
    
    File.write!(@next_file, content)
  end

  defp generate_schedule_overlay do
    # Get upcoming videos from playlist or catalog
    upcoming = get_upcoming_videos(5)
    content = build_schedule_html(upcoming)
    File.write!(@schedule_file, content)
  end

  defp get_upcoming_videos(limit) do
    # Get from playlist if available, otherwise random from catalog
    playlist = State.get_playlist()
    
    if length(playlist) >= limit do
      Enum.take(playlist, limit)
    else
      # Get random videos from catalog
      recently_played = State.get_recently_played(100)
      
      Catalog.list_media(%{"sort" => "random", "page" => 1})
      |> Enum.reject(fn video -> video.id in recently_played end)
      |> Enum.take(limit)
      |> Enum.map(fn media ->
        %{
          id: media.id,
          title: media.title,
          creator: media.creator,
          year: media.year
        }
      end)
    end
  end

  defp build_current_html(video) do
    """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          margin: 0;
          padding: 20px;
          font-family: 'Courier New', monospace;
          background: linear-gradient(135deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.7) 100%);
          color: #00ff00;
          text-shadow: 0 0 10px #00ff00;
        }
        .container {
          animation: fadeIn 1s;
        }
        .label {
          font-size: 14px;
          color: #00ffff;
          margin-bottom: 5px;
        }
        .title {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 10px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="label">NOW PLAYING</div>
        <div class="title">#{html_escape(video[:title] || video["title"] || "Unknown")}</div>
      </div>
    </body>
    </html>
    """
  end

  defp build_empty_current_html do
    """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          margin: 0;
          padding: 20px;
          font-family: 'Courier New', monospace;
          background: transparent;
        }
      </style>
    </head>
    <body>
    </body>
    </html>
    """
  end

  defp build_next_html(video) do
    """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          margin: 0;
          padding: 20px;
          font-family: 'Courier New', monospace;
          background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.6) 100%);
          color: #ffff00;
          text-shadow: 0 0 8px #ffff00;
        }
        .container {
          animation: pulse 2s infinite;
        }
        .label {
          font-size: 12px;
          color: #ff00ff;
          margin-bottom: 5px;
        }
        .title {
          font-size: 18px;
          margin-bottom: 5px;
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.8; }
          50% { opacity: 1; }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="label">UP NEXT</div>
        <div class="title">#{html_escape(video[:title] || video["title"] || "Unknown")}</div>
      </div>
    </body>
    </html>
    """
  end

  defp build_empty_next_html do
    """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          margin: 0;
          padding: 20px;
          font-family: 'Courier New', monospace;
          background: transparent;
        }
      </style>
    </head>
    <body>
    </body>
    </html>
    """
  end

  defp build_schedule_html(videos) do
    items = videos
    |> Enum.with_index(1)
    |> Enum.map(fn {video, index} ->
      """
      <div class="item">
        <span class="number">#{index}.</span>
        <span class="title">#{html_escape(video[:title] || video["title"] || "Unknown")}</span>
      </div>
      """
    end)
    |> Enum.join("\n")
    
    """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          margin: 0;
          padding: 15px;
          font-family: 'Courier New', monospace;
          background: linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.8) 100%);
          color: #00ffff;
        }
        .header {
          font-size: 16px;
          color: #ff00ff;
          margin-bottom: 10px;
          text-shadow: 0 0 10px #ff00ff;
        }
        .item {
          font-size: 14px;
          margin-bottom: 8px;
          padding-left: 10px;
          opacity: 0;
          animation: slideIn 0.5s forwards;
        }
        .item:nth-child(2) { animation-delay: 0.1s; }
        .item:nth-child(3) { animation-delay: 0.2s; }
        .item:nth-child(4) { animation-delay: 0.3s; }
        .item:nth-child(5) { animation-delay: 0.4s; }
        .item:nth-child(6) { animation-delay: 0.5s; }
        .number {
          color: #ffff00;
          margin-right: 10px;
        }
        .title {
          color: #00ff00;
          text-shadow: 0 0 5px #00ff00;
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      </style>
    </head>
    <body>
      <div class="header">COMING UP</div>
      #{items}
    </body>
    </html>
    """
  end

  defp html_escape(text) when is_binary(text) do
    text
    |> String.replace("&", "&amp;")
    |> String.replace("<", "&lt;")
    |> String.replace(">", "&gt;")
    |> String.replace("\"", "&quot;")
    |> String.replace("'", "&#39;")
  end
  
  defp html_escape(text), do: html_escape(to_string(text))
end