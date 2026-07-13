package startupretry

import (
	"errors"
	"strings"
	"testing"
)

func TestRetryEventuallySucceeds(t *testing.T) {
	t.Parallel()

	attempts := 0
	err := Retry("dependency", 5, 0, func() error {
		attempts++
		if attempts < 3 {
			return errors.New("not ready")
		}
		return nil
	})
	if err != nil {
		t.Fatalf("Retry() error = %v", err)
	}
	if attempts != 3 {
		t.Fatalf("attempts = %d, want 3", attempts)
	}
}

func TestRetryReturnsLastError(t *testing.T) {
	t.Parallel()

	attempts := 0
	err := Retry("dependency", 3, 0, func() error {
		attempts++
		return errors.New("still not ready")
	})
	if err == nil {
		t.Fatal("Retry() error = nil, want error")
	}
	if attempts != 3 {
		t.Fatalf("attempts = %d, want 3", attempts)
	}
	if !strings.Contains(err.Error(), "still not ready") {
		t.Fatalf("error = %q, want last error to be preserved", err)
	}
}
