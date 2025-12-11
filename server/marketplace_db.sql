-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Хост: 127.0.0.1
-- Время создания: Дек 11 2025 г., 21:14
-- Версия сервера: 10.4.32-MariaDB
-- Версия PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `marketplace_db`
--

-- --------------------------------------------------------

--
-- Структура таблицы `import_jobs`
--

CREATE TABLE `import_jobs` (
  `id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `status` varchar(50) DEFAULT NULL,
  `source_url` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `products`
--

CREATE TABLE `products` (
  `id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `price` decimal(10,2) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `product_characteristics`
--

CREATE TABLE `product_characteristics` (
  `id` varchar(255) NOT NULL,
  `product_id` varchar(255) NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `product_features`
--

CREATE TABLE `product_features` (
  `product_id` varchar(255) NOT NULL,
  `features` text DEFAULT NULL,
  `embedding` text DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `product_images`
--

CREATE TABLE `product_images` (
  `id` varchar(255) NOT NULL,
  `product_id` varchar(255) NOT NULL,
  `url` varchar(500) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `product_segments`
--

CREATE TABLE `product_segments` (
  `product_id` varchar(255) NOT NULL,
  `segment_id` varchar(255) NOT NULL,
  `score` decimal(5,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `reviews`
--

CREATE TABLE `reviews` (
  `id` varchar(255) NOT NULL,
  `product_id` varchar(255) NOT NULL,
  `rating` int(11) NOT NULL CHECK (`rating` >= 1 and `rating` <= 5),
  `text` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `review_nlp`
--

CREATE TABLE `review_nlp` (
  `review_id` varchar(255) NOT NULL,
  `sentiment` decimal(3,2) NOT NULL,
  `topics` text DEFAULT NULL,
  `analyzed_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `segments`
--

CREATE TABLE `segments` (
  `id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `sellers`
--

CREATE TABLE `sellers` (
  `id` varchar(255) NOT NULL,
  `user_id` varchar(255) NOT NULL,
  `store_name` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `storefronts`
--

CREATE TABLE `storefronts` (
  `id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `status` varchar(50) DEFAULT NULL,
  `store_url` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `storefront_settings`
--

CREATE TABLE `storefront_settings` (
  `seller_id` varchar(255) NOT NULL,
  `theme` varchar(50) NOT NULL DEFAULT 'default',
  `color_scheme` varchar(100) DEFAULT NULL,
  `logo_url` varchar(500) DEFAULT NULL,
  `domain` varchar(255) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `store_pages`
--

CREATE TABLE `store_pages` (
  `id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `slug` varchar(100) NOT NULL,
  `title` varchar(255) NOT NULL,
  `layout_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`layout_json`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `store_products`
--

CREATE TABLE `store_products` (
  `id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `original_product_id` varchar(255) NOT NULL,
  `custom_title` varchar(255) DEFAULT NULL,
  `custom_price` decimal(10,2) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `display_order` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `store_product_descriptions`
--

CREATE TABLE `store_product_descriptions` (
  `store_product_id` varchar(255) NOT NULL,
  `custom_description` text DEFAULT NULL,
  `seo_text` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `store_product_images`
--

CREATE TABLE `store_product_images` (
  `id` varchar(255) NOT NULL,
  `store_product_id` varchar(255) NOT NULL,
  `url` varchar(500) NOT NULL,
  `is_main` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_login` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `created_at`, `last_login`, `is_active`) VALUES
(3, 'jon_doe', 'j@example.com', 'scrypt:32768:8:1$rz075o92DGbGjk5U$bfd67b7645a1164f44c85f64caffd0a3ff2716f0fe893f1017dd9b1f4c9e1c3b9273babaab6e9046fbf60a1188b48ac8083d01d09a7a3aa57fad013f85d9adfa', '2025-12-11 15:35:09', '2025-12-11 15:36:25', 1);

-- --------------------------------------------------------

--
-- Структура таблицы `users_old`
--

CREATE TABLE `users_old` (
  `id` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `users_old`
--

INSERT INTO `users_old` (`id`, `email`, `password_hash`, `created_at`) VALUES
('0036f6c1-0a5f-4d2d-8742-bf1972063b35', 'og@mil.ru', '$2b$12$Fem.tGq37zNxeyg1uKKUnOuRHojh1BDqu8C6XT/AdyuCDUWPz7oGm', '2025-12-10 11:23:35'),
('24a5b6ec-5c00-4797-8c07-fcb49311a2a3', 'seller@example.com', '$2b$12$hH4Hs35.Ll5Ib3Y7/Adz9ex5nTDFFBi3ki./ceBJ20FTBkIsHWUuS', '2025-12-10 11:41:01'),
('52f4e687-748a-4ae1-96fa-9df2d262b3c1', 'sr@example.com', '$2b$12$cXesCoxFh1lvS70qg8QT9ebWb4r6M3XplhCQf/PrUnEzPgzT.hR1G', '2025-12-11 08:39:54'),
('654255ae-94c0-4647-ac74-61e63d7908de', 'seller.com', '$2b$12$Puiuk8DRmgARSyBmdQFh6ehvAfHSsYOENvDHL047zYK09Ce9vqN32', '2025-12-11 05:00:46'),
('9332b8cf-1c78-4bc3-9a49-c1f28b702f90', 'Ya@mail.ru', '$2b$12$j.rCpFWb2MUKD8a5XsiTvO4oigdc/SS6MUQt4FdZy9Mv//fbx73hG', '2025-12-11 05:51:09'),
('a971b93c-8d59-4bf5-a2d4-a178a00598f4', 'selr@example.com', '$2b$12$oUydIKIyM5Uj1WBLbn2ly.1TlHEFttXJ7HYUjqYBA.mYQ9pw3F5.2', '2025-12-10 11:41:28'),
('b20a88c3-35c3-4bad-814f-19b2a6d67298', 'ogiii@mil.ru', '$2b$12$UUqO8S.CZQQFtRQqV73KleP3R92aa4kKerswCinn0UTomapIVXuVy', '2025-12-10 11:27:38');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `import_jobs`
--
ALTER TABLE `import_jobs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `seller_id` (`seller_id`);

--
-- Индексы таблицы `products`
--
ALTER TABLE `products`
  ADD PRIMARY KEY (`id`),
  ADD KEY `seller_id` (`seller_id`);

--
-- Индексы таблицы `product_characteristics`
--
ALTER TABLE `product_characteristics`
  ADD PRIMARY KEY (`id`),
  ADD KEY `product_id` (`product_id`);

--
-- Индексы таблицы `product_features`
--
ALTER TABLE `product_features`
  ADD PRIMARY KEY (`product_id`);

--
-- Индексы таблицы `product_images`
--
ALTER TABLE `product_images`
  ADD PRIMARY KEY (`id`),
  ADD KEY `product_id` (`product_id`);

--
-- Индексы таблицы `product_segments`
--
ALTER TABLE `product_segments`
  ADD PRIMARY KEY (`product_id`,`segment_id`),
  ADD KEY `segment_id` (`segment_id`);

--
-- Индексы таблицы `reviews`
--
ALTER TABLE `reviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `product_id` (`product_id`);

--
-- Индексы таблицы `review_nlp`
--
ALTER TABLE `review_nlp`
  ADD PRIMARY KEY (`review_id`);

--
-- Индексы таблицы `segments`
--
ALTER TABLE `segments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `seller_id` (`seller_id`);

--
-- Индексы таблицы `sellers`
--
ALTER TABLE `sellers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Индексы таблицы `storefronts`
--
ALTER TABLE `storefronts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `seller_id` (`seller_id`);

--
-- Индексы таблицы `storefront_settings`
--
ALTER TABLE `storefront_settings`
  ADD PRIMARY KEY (`seller_id`);

--
-- Индексы таблицы `store_pages`
--
ALTER TABLE `store_pages`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `seller_id` (`seller_id`,`slug`);

--
-- Индексы таблицы `store_products`
--
ALTER TABLE `store_products`
  ADD PRIMARY KEY (`id`),
  ADD KEY `seller_id` (`seller_id`),
  ADD KEY `original_product_id` (`original_product_id`);

--
-- Индексы таблицы `store_product_descriptions`
--
ALTER TABLE `store_product_descriptions`
  ADD PRIMARY KEY (`store_product_id`);

--
-- Индексы таблицы `store_product_images`
--
ALTER TABLE `store_product_images`
  ADD PRIMARY KEY (`id`),
  ADD KEY `store_product_id` (`store_product_id`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Индексы таблицы `users_old`
--
ALTER TABLE `users_old`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `import_jobs`
--
ALTER TABLE `import_jobs`
  ADD CONSTRAINT `import_jobs_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `products`
--
ALTER TABLE `products`
  ADD CONSTRAINT `products_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `product_characteristics`
--
ALTER TABLE `product_characteristics`
  ADD CONSTRAINT `product_characteristics_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `product_features`
--
ALTER TABLE `product_features`
  ADD CONSTRAINT `product_features_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `product_images`
--
ALTER TABLE `product_images`
  ADD CONSTRAINT `product_images_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `product_segments`
--
ALTER TABLE `product_segments`
  ADD CONSTRAINT `product_segments_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `product_segments_ibfk_2` FOREIGN KEY (`segment_id`) REFERENCES `segments` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `reviews`
--
ALTER TABLE `reviews`
  ADD CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `review_nlp`
--
ALTER TABLE `review_nlp`
  ADD CONSTRAINT `review_nlp_ibfk_1` FOREIGN KEY (`review_id`) REFERENCES `reviews` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `segments`
--
ALTER TABLE `segments`
  ADD CONSTRAINT `segments_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `sellers`
--
ALTER TABLE `sellers`
  ADD CONSTRAINT `sellers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_old` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `storefronts`
--
ALTER TABLE `storefronts`
  ADD CONSTRAINT `storefronts_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `storefront_settings`
--
ALTER TABLE `storefront_settings`
  ADD CONSTRAINT `storefront_settings_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `store_pages`
--
ALTER TABLE `store_pages`
  ADD CONSTRAINT `store_pages_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `store_products`
--
ALTER TABLE `store_products`
  ADD CONSTRAINT `store_products_ibfk_1` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `store_products_ibfk_2` FOREIGN KEY (`original_product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `store_product_descriptions`
--
ALTER TABLE `store_product_descriptions`
  ADD CONSTRAINT `store_product_descriptions_ibfk_1` FOREIGN KEY (`store_product_id`) REFERENCES `store_products` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `store_product_images`
--
ALTER TABLE `store_product_images`
  ADD CONSTRAINT `store_product_images_ibfk_1` FOREIGN KEY (`store_product_id`) REFERENCES `store_products` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
