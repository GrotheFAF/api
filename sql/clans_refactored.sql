CREATE TABLE `clan_list` (
  `clan_id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` int(1) NOT NULL DEFAULT '0',
  `clan_name` varchar(40) NOT NULL,
  `clan_tag` varchar(3) DEFAULT NULL,
  `clan_founder_id` mediumint(8) DEFAULT NULL,
  `clan_desc` text,
  PRIMARY KEY (`clan_id`)
);

CREATE TABLE `clan_members` (
  `clan_id` int(11) NOT NULL,
  `player_id` int(11) NOT NULL,
  `join_clan_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`clan_id`,`player_id`),
  KEY `player_id` (`player_id`),
  CONSTRAINT `clan_members_ibfk_1` FOREIGN KEY (`clan_id`) REFERENCES `clan_list` (`clan_id`)
);

CREATE TABLE `clan_leader` (
  `clan_id` int(11) NOT NULL,
  `player_id` int(11) NOT NULL,
  `became_leader_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`clan_id`),
  CONSTRAINT `clan_leader_ibfk_1` FOREIGN KEY (`clan_id`) REFERENCES `clan_list` (`clan_id`)
);
