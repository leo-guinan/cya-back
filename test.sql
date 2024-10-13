-- SELECT DISTINCT "type",  count(1) FROM "prelo_messagetoconfirm" WHERE conversation_uuid = 'HOEx5VA' GROUP BY "type";


UPDATE "User" SET "submindPending" = false WHERE "submindPending" = true;