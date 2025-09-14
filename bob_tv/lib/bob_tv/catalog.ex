defmodule BobTv.Catalog do
  @moduledoc """
  The Catalog context for managing media library items
  """

  import Ecto.Query, warn: false
  alias BobTv.Repo
  alias BobTv.Catalog.Media

  def list_media(params \\ %{}) do
    query = from(m in Media)

    query
    |> apply_filters(params)
    |> apply_sorting(params)
    |> paginate(params)
    |> Repo.all()
  end

  def count_media(params \\ %{}) do
    query = from(m in Media)

    query
    |> apply_filters(params)
    |> Repo.aggregate(:count, :id)
  end

  def get_media!(id) do
    Repo.get!(Media, id)
  end

  def get_similar_media(media, limit \\ 12) do
    from(m in Media,
      where: m.id != ^media.id,
      where: m.creator == ^media.creator or m.mediatype == ^media.mediatype,
      order_by: fragment("RANDOM()"),
      limit: ^limit
    )
    |> Repo.all()
  end

  def get_type_counts do
    from(m in Media,
      group_by: m.mediatype,
      select: {m.mediatype, count(m.id)}
    )
    |> Repo.all()
    |> Enum.into(%{})
  end

  def get_distinct_years do
    from(m in Media,
      where: not is_nil(m.year),
      distinct: true,
      order_by: [desc: m.year],
      select: m.year
    )
    |> Repo.all()
  end

  def get_random_media do
    from(m in Media,
      order_by: fragment("RANDOM()"),
      limit: 1
    )
    |> Repo.one()
  end

  def get_programming_ideas do
    ideas = []

    # Late Night Obscura
    obscure_items = from(m in Media,
      where: m.downloads < 50,
      order_by: fragment("RANDOM()"),
      limit: 3
    ) |> Repo.all()

    ideas = if obscure_items != [] do
      [%{
        block: "Late Night Obscura",
        description: "Deep cuts nobody watches",
        items: obscure_items
      } | ideas]
    else
      ideas
    end

    # Popular Hour
    popular_items = from(m in Media,
      order_by: [desc: m.downloads],
      limit: 3
    ) |> Repo.all()

    ideas = if popular_items != [] do
      [%{
        block: "Prime Time Favorites",
        description: "Most downloaded content",
        items: popular_items
      } | ideas]
    else
      ideas
    end

    # Vintage Vault
    vintage_items = from(m in Media,
      where: m.year < 1990 and not is_nil(m.year),
      order_by: fragment("RANDOM()"),
      limit: 3
    ) |> Repo.all()

    if vintage_items != [] do
      [%{
        block: "Vintage Vault",
        description: "Pre-1990 classics",
        items: vintage_items
      } | ideas]
    else
      ideas
    end
  end

  def get_stats do
    total = Repo.aggregate(Media, :count, :id)

    by_type = from(m in Media,
      group_by: m.mediatype,
      select: {m.mediatype, count(m.id)}
    )
    |> Repo.all()
    |> Enum.into(%{})

    total_size = Repo.aggregate(Media, :sum, :item_size)
    total_downloads = Repo.aggregate(Media, :sum, :downloads)

    by_year = from(m in Media,
      where: not is_nil(m.year),
      group_by: m.year,
      order_by: m.year,
      select: {m.year, count(m.id)}
    )
    |> Repo.all()
    |> Enum.into(%{})

    %{
      total: total,
      by_type: by_type,
      total_size: total_size,
      total_downloads: total_downloads,
      by_year: by_year
    }
  end

  defp apply_filters(query, params) do
    query
    |> filter_by_type(params["type"])
    |> filter_by_search(params["search"])
    |> filter_by_year(params["year"])
  end

  defp filter_by_type(query, nil), do: query
  defp filter_by_type(query, "all"), do: query
  defp filter_by_type(query, type) do
    from(m in query, where: m.mediatype == ^type)
  end

  defp filter_by_search(query, nil), do: query
  defp filter_by_search(query, ""), do: query
  defp filter_by_search(query, search) do
    search_term = "%#{search}%"
    from(m in query,
      where: ilike(m.title, ^search_term) or
             ilike(m.description, ^search_term) or
             ilike(m.creator, ^search_term)
    )
  end

  defp filter_by_year(query, nil), do: query
  defp filter_by_year(query, ""), do: query
  defp filter_by_year(query, year) when is_binary(year) do
    case Integer.parse(year) do
      {year_int, ""} -> from(m in query, where: m.year == ^year_int)
      _ -> query
    end
  end
  defp filter_by_year(query, year) when is_integer(year) do
    from(m in query, where: m.year == ^year)
  end

  defp apply_sorting(query, %{"sort" => sort}) do
    case sort do
      "downloads" -> from(m in query, order_by: [desc: m.downloads])
      "date" -> from(m in query, order_by: [desc: m.date])
      "title" -> from(m in query, order_by: [asc: m.title])
      "size" -> from(m in query, order_by: [desc: m.item_size])
      _ -> from(m in query, order_by: fragment("RANDOM()"))
    end
  end
  defp apply_sorting(query, _), do: from(m in query, order_by: fragment("RANDOM()"))

  defp paginate(query, %{"page" => page} = params) when is_binary(page) do
    case Integer.parse(page) do
      {page_num, ""} -> paginate(query, Map.put(params, "page", page_num))
      _ -> paginate(query, Map.delete(params, "page"))
    end
  end
  defp paginate(query, %{"page" => page}) when is_integer(page) do
    per_page = 48
    offset = (max(page, 1) - 1) * per_page

    from(m in query,
      limit: ^per_page,
      offset: ^offset
    )
  end
  defp paginate(query, _) do
    from(m in query, limit: 48)
  end
end