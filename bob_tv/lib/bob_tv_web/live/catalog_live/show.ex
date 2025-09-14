defmodule BobTvWeb.CatalogLive.Show do
  use BobTvWeb, :live_view
  alias BobTv.Catalog

  @impl true
  def mount(_params, _session, socket) do
    {:ok, socket}
  end

  @impl true
  def handle_params(%{"id" => id}, _url, socket) do
    media = Catalog.get_media!(id)
    similar_items = Catalog.get_similar_media(media)

    {:noreply,
     socket
     |> assign(:page_title, "#{media.title} - The Bobbing Channel")
     |> assign(:item, media)
     |> assign(:similar, similar_items)}
  end

  @impl true
  def handle_event("copy_link", %{"id" => id}, socket) do
    {:noreply, push_event(socket, "copy_to_clipboard", %{
      text: "http://localhost:4000/catalog/#{id}"
    })}
  end

  @impl true
  def handle_event("add_to_playlist", %{"id" => id}, socket) do
    {:noreply, push_event(socket, "add_to_playlist", %{id: id})}
  end

  def format_number(nil), do: "0"
  def format_number(num) when is_integer(num) do
    num
    |> Integer.to_string()
    |> String.reverse()
    |> String.replace(~r/(\d{3})(?=\d)/, "\\1,")
    |> String.reverse()
  end
  def format_number(num), do: format_number(trunc(num))

  def format_size(nil), do: "Unknown"
  def format_size(bytes) do
    cond do
      bytes < 1024 ->
        "#{bytes} B"
      bytes < 1024 * 1024 ->
        "#{Float.round(bytes / 1024, 1)} KB"
      bytes < 1024 * 1024 * 1024 ->
        "#{Float.round(bytes / (1024 * 1024), 1)} MB"
      bytes < 1024 * 1024 * 1024 * 1024 ->
        "#{Float.round(bytes / (1024 * 1024 * 1024), 1)} GB"
      true ->
        "#{Float.round(bytes / (1024 * 1024 * 1024 * 1024), 1)} TB"
    end
  end
end