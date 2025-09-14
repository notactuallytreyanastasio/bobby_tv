defmodule BobTv.Repo do
  use Ecto.Repo,
    otp_app: :bob_tv,
    adapter: Ecto.Adapters.SQLite3
end
