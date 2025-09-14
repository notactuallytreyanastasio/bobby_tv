defmodule BobTvWeb.PageController do
  use BobTvWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
