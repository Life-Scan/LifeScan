-- Execute no MySQL Workbench usando uma conexao de administrador.
-- Mantem o banco lifescan existente sem alteracoes.
CREATE DATABASE IF NOT EXISTS lifescan_devtests
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON lifescan_devtests.* TO 'lifescan'@'localhost';
