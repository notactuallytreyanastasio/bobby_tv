defmodule BobTvWeb.CatalogLive.Index do
  use BobTvWeb, :live_view
  alias BobTv.Catalog

  @per_page 48

  @impl true
  def mount(_params, _session, socket) do
    {:ok, socket}
  end

  @impl true
  def handle_params(params, _url, socket) do
    {:noreply, apply_action(socket, socket.assigns.live_action, params)}
  end

  defp apply_action(socket, :index, params) do
    page = get_page(params)

    items = Catalog.list_media(params)
    total_items = Catalog.count_media(params)
    total_in_db = Catalog.count_media()
    type_counts = Catalog.get_type_counts()
    years = Catalog.get_distinct_years()

    programming_ideas = if page == 1 and params["search"] in [nil, ""] do
      Catalog.get_programming_ideas()
    else
      []
    end

    total_pages = div(total_items + @per_page - 1, @per_page)

    socket
    |> assign(:page_title, "The Bobbing Channel - Catalog Explorer")
    |> assign(:items, items)
    |> assign(:total_items, total_items)
    |> assign(:total_in_db, total_in_db)
    |> assign(:type_counts, type_counts)
    |> assign(:years, years)
    |> assign(:current_type, params["type"] || "all")
    |> assign(:current_sort, params["sort"] || "random")
    |> assign(:current_search, params["search"] || "")
    |> assign(:current_year, params["year"] || "")
    |> assign(:current_page, page)
    |> assign(:total_pages, max(total_pages, 1))
    |> assign(:programming_ideas, programming_ideas)
  end

  @impl true
  def handle_event("filter", params, socket) do
    {:noreply, push_patch(socket, to: ~p"/catalog?#{URI.encode_query(params)}")}
  end

  @impl true
  def handle_event("random", _params, socket) do
    case Catalog.get_random_media() do
      nil ->
        {:noreply, put_flash(socket, :error, "No items found")}
      media ->
        {:noreply, push_navigate(socket, to: ~p"/catalog/#{media.id}")}
    end
  end

  @impl true
  def handle_event("toggle_night_mode", _params, socket) do
    # This would typically store in session or user preferences
    {:noreply, push_event(socket, "toggle_night_mode", %{})}
  end

  defp get_page(params) do
    case Integer.parse(params["page"] || "1") do
      {page, ""} when page > 0 -> page
      _ -> 1
    end
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

  def build_query(page, type, sort, search, year) do
    params = []
    params = if page && page != 1, do: [{"page", page} | params], else: params
    params = if type && type != "all", do: [{"type", type} | params], else: params
    params = if sort && sort != "random", do: [{"sort", sort} | params], else: params
    params = if search && search != "", do: [{"search", search} | params], else: params
    params = if year && year != "", do: [{"year", year} | params], else: params

    URI.encode_query(params)
  end
end