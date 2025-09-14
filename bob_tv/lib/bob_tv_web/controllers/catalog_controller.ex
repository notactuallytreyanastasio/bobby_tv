defmodule BobTvWeb.CatalogController do
  use BobTvWeb, :controller
  alias BobTv.Catalog

  def stats(conn, _params) do
    stats = Catalog.get_stats()
    json(conn, stats)
  end
end