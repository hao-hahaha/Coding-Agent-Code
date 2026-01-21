import { Redis } from "@upstash/redis";

// Configuration
const TOKEN_KEY_PREFIX = "chat:token:";
const USER_KEY_PREFIX = "chat:users:";
const NEW_USER_TTL_SECONDS = 7776000; // 90 days (previously 30 days)
const NEW_TOKEN_GRACE_PERIOD = 86400 * 365; // 365 days (previously 7 days)
const SCAN_COUNT = 100; // Number of keys to fetch per SCAN command

// Initialize Redis client
const redis = new Redis({
  url: process.env.REDIS_KV_REST_API_URL,
  token: process.env.REDIS_KV_REST_API_TOKEN,
});

async function migrateTokenTTLs() {
  if (
    !process.env.REDIS_KV_REST_API_URL ||
    !process.env.REDIS_KV_REST_API_TOKEN
  ) {
    console.error(
      "Error: REDIS_KV_REST_API_URL and REDIS_KV_REST_API_TOKEN environment variables must be set."
    );
    process.exit(1);
  }

  console.log("Starting migration to update token and user TTLs...");
  console.log(`New user/token TTL: ${NEW_USER_TTL_SECONDS} seconds (90 days)`);
  console.log(`New grace period: ${NEW_TOKEN_GRACE_PERIOD} seconds (365 days)`);
  console.log("---");

  let tokensUpdated = 0;
  let lastTokensUpdated = 0;
  let usersUpdated = 0;

  try {
    // Update active tokens
    console.log("\n1. Updating active tokens...");
    let cursor = "0";
    do {
      const [nextCursor, keys] = await redis.scan(cursor, {
        match: `${TOKEN_KEY_PREFIX}*`,
        count: SCAN_COUNT,
      });
      cursor = nextCursor;

      if (keys.length > 0) {
        for (const key of keys) {
          // Skip "last:" tokens for now
          if (key.includes(":last:")) continue;

          const ttl = await redis.ttl(key);
          if (ttl > 0) {
            // Only update if key has a TTL (not -1 which means no expiry)
            // Calculate new TTL based on the assumption that the token should live 90 days from creation
            // We'll extend the current TTL by the difference (60 days)
            const currentTTL = ttl;
            const extensionDays = 60; // 90 days - 30 days
            const extensionSeconds = extensionDays * 24 * 60 * 60;
            const newTTL = Math.min(currentTTL + extensionSeconds, NEW_USER_TTL_SECONDS);
            
            await redis.expire(key, newTTL);
            tokensUpdated++;
            console.log(`Updated token ${key}: TTL ${ttl}s -> ${newTTL}s`);
          }
        }
      }
    } while (cursor !== "0");

    // Update last tokens (used for grace period)
    console.log("\n2. Updating last tokens (grace period tokens)...");
    cursor = "0";
    do {
      const [nextCursor, keys] = await redis.scan(cursor, {
        match: `${TOKEN_KEY_PREFIX}last:*`,
        count: SCAN_COUNT,
      });
      cursor = nextCursor;

      if (keys.length > 0) {
        for (const key of keys) {
          const ttl = await redis.ttl(key);
          if (ttl > 0) {
            // Last tokens should have TTL of original expiry + grace period
            // Extend by the difference in grace periods (358 days)
            const gracePeriodExtension = 358 * 24 * 60 * 60; // 365 days - 7 days
            const newTTL = Math.min(ttl + gracePeriodExtension, NEW_USER_TTL_SECONDS + NEW_TOKEN_GRACE_PERIOD);
            
            await redis.expire(key, newTTL);
            lastTokensUpdated++;
            console.log(`Updated last token ${key}: TTL ${ttl}s -> ${newTTL}s`);
          }
        }
      }
    } while (cursor !== "0");

    // Remove TTL from user records (make them permanent)
    console.log("\n3. Removing TTL from user records (making them permanent)...");
    cursor = "0";
    do {
      const [nextCursor, keys] = await redis.scan(cursor, {
        match: `${USER_KEY_PREFIX}*`,
        count: SCAN_COUNT,
      });
      cursor = nextCursor;

      if (keys.length > 0) {
        for (const key of keys) {
          const ttl = await redis.ttl(key);
          if (ttl > 0) {
            // Remove TTL by using PERSIST command
            await redis.persist(key);
            usersUpdated++;
            console.log(`Removed TTL from user ${key} (was ${ttl}s, now permanent)`);
          }
        }
      }
    } while (cursor !== "0");

    console.log("\n--- Migration Complete ---");
    console.log(`Active tokens updated: ${tokensUpdated}`);
    console.log(`Last tokens (grace period) updated: ${lastTokensUpdated}`);
    console.log(`User records made permanent: ${usersUpdated}`);
    console.log(`Total records updated: ${tokensUpdated + lastTokensUpdated + usersUpdated}`);
    
    console.log("\nNote:");
    console.log("- Active tokens: extended by ~60 days (to reach 90-day total)");
    console.log("- Last tokens: extended by ~358 days (to reach 455-day total)");
    console.log("- User records: TTL removed - they now persist forever");

  } catch (error) {
    console.error("\n--- Error during migration ---");
    console.error(error);
    process.exit(1);
  }
}

migrateTokenTTLs();