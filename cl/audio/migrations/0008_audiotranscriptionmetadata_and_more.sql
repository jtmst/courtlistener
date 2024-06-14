BEGIN;
--
-- Create model AudioTranscriptionMetadata
--
CREATE TABLE "audio_audiotranscriptionmetadata" ("id" integer NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, "metadata" jsonb NOT NULL);
--
-- Remove field stt_google_response from audio
--
ALTER TABLE "audio_audio" DROP COLUMN "stt_google_response" CASCADE;
--
-- Remove field stt_google_response from audioevent
--
ALTER TABLE "audio_audioevent" DROP COLUMN "stt_google_response" CASCADE;
--
-- Add field stt_source to audio
--
ALTER TABLE "audio_audio" ADD COLUMN "stt_source" smallint NULL;
--
-- Add field stt_transcript to audio
--
ALTER TABLE "audio_audio" ADD COLUMN "stt_transcript" text DEFAULT '' NOT NULL;
ALTER TABLE "audio_audio" ALTER COLUMN "stt_transcript" DROP DEFAULT;
--
-- Add field stt_source to audioevent
--
ALTER TABLE "audio_audioevent" ADD COLUMN "stt_source" smallint NULL;
--
-- Add field stt_transcript to audioevent
--
ALTER TABLE "audio_audioevent" ADD COLUMN "stt_transcript" text DEFAULT '' NOT NULL;
ALTER TABLE "audio_audioevent" ALTER COLUMN "stt_transcript" DROP DEFAULT;
--
-- Add field audio to audiotranscriptionmetadata
--
ALTER TABLE "audio_audiotranscriptionmetadata" ADD COLUMN "audio_id" integer NOT NULL CONSTRAINT "audio_audiotranscrip_audio_id_22f57b06_fk_audio_aud" REFERENCES "audio_audio"("id") DEFERRABLE INITIALLY DEFERRED; SET CONSTRAINTS "audio_audiotranscrip_audio_id_22f57b06_fk_audio_aud" IMMEDIATE;
CREATE INDEX "audio_audiotranscriptionmetadata_audio_id_22f57b06" ON "audio_audiotranscriptionmetadata" ("audio_id");
COMMIT;
