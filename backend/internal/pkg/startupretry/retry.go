package startupretry

import (
	"fmt"
	"log"
	"time"
)

// Retry runs fn until it succeeds or the retry budget is exhausted.
// It is intended for startup paths where external dependencies may still be
// booting (for example, PostgreSQL/Redis in Coolify).
func Retry(name string, attempts int, delay time.Duration, fn func() error) error {
	if attempts < 1 {
		attempts = 1
	}
	if delay < 0 {
		delay = 0
	}

	var lastErr error
	for attempt := 1; attempt <= attempts; attempt++ {
		if err := fn(); err != nil {
			lastErr = err
			if attempt == attempts {
				break
			}
			log.Printf("[startup] %s not ready (attempt %d/%d): %v; retrying in %s", name, attempt, attempts, err, delay)
			if delay > 0 {
				time.Sleep(delay)
			}
			continue
		}
		return nil
	}

	if lastErr == nil {
		return fmt.Errorf("%s failed to start", name)
	}
	return fmt.Errorf("%s failed after %d attempts: %w", name, attempts, lastErr)
}
