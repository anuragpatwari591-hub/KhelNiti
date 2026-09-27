# Services (not yet extracted)

The spec calls for `live-score-service`, `prediction-service`,
`news-service`, `market-service`, and `notification-service` as separate
deployables. Today their logic lives inside `backend/app` as modules with
the same boundaries these services would have
(`backend/app/websocket` = live-score, `backend/app/predictions` =
prediction-service, `backend/app/news` = news-service,
`backend/app/markets` = market-service; there is no notification-service
yet at all). See
[docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md#current-system-shape) for
why: standing up five deployables and a message broker before there is
real load or team ownership requiring the split would add operational
complexity with no present benefit, and the module boundaries already
mirror the eventual service boundaries so extraction is a deployment
change later, not a rewrite.

Each subdirectory here is a placeholder for that future extraction.
