-- Migration script to add star_rating column to feedback table
ALTER TABLE feedback ADD COLUMN star_rating INTEGER;
