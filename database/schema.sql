CREATE TABLE IF NOT EXISTS `blacklist` (
  `user_id` varchar(20) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `wordchain_games` (
  `channel_id` varchar(20) NOT NULL PRIMARY KEY,
  `guild_id` varchar(20) NOT NULL,
  `current_word` varchar(255) NOT NULL,
  `current_user_id` varchar(20),
  `last_user_id` varchar(20),
  `word_count` int(11) NOT NULL DEFAULT 0,
  `base_score` int(11) NOT NULL DEFAULT 2,
  `y_count` int(11) NOT NULL DEFAULT 0,
  `is_active` BOOLEAN NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `wordchain_session_scores` (
  `channel_id` varchar(20) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `score` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`channel_id`, `user_id`)
);

CREATE TABLE IF NOT EXISTS `wordchain_used_words` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `channel_id` varchar(20) NOT NULL,
  `word` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `wordchain_scores` (
  `user_id` varchar(20) NOT NULL,
  `guild_id` varchar(20) NOT NULL,
  `score` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`user_id`, `guild_id`)
);