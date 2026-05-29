package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// HTTPClient wraps calls to the MT5 FastAPI service.
type HTTPClient struct {
	Base string
	HTTP *http.Client
}

func NewHTTPClient(base string) *HTTPClient {
	return &HTTPClient{
		Base: base,
		HTTP: &http.Client{Timeout: 30 * time.Second},
	}
}

func (c *HTTPClient) Get(path string, query url.Values) (string, error) {
	u := c.Base + path
	if len(query) > 0 {
		u += "?" + query.Encode()
	}
	resp, err := c.HTTP.Get(u)
	if err != nil {
		return "", fmt.Errorf("GET %s: %w", u, err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}
	return string(body), nil
}

func (c *HTTPClient) Post(path string, payload any) (string, error) {
	var body io.Reader
	if payload != nil {
		b, err := json.Marshal(payload)
		if err != nil {
			return "", fmt.Errorf("marshal: %w", err)
		}
		body = bytes.NewReader(b)
	}
	req, err := http.NewRequest("POST", c.Base+path, body)
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return "", fmt.Errorf("POST %s: %w", path, err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(b))
	}
	return string(b), nil
}

// qv constructs url.Values from alternating key/value pairs. Values that are
// the empty string are omitted entirely. Numeric values are formatted compactly.
func qv(pairs ...any) url.Values {
	v := url.Values{}
	for i := 0; i+1 < len(pairs); i += 2 {
		key, _ := pairs[i].(string)
		switch val := pairs[i+1].(type) {
		case string:
			if val != "" {
				v.Set(key, val)
			}
		case int:
			if val != 0 {
				v.Set(key, strconv.Itoa(val))
			}
		case int64:
			if val != 0 {
				v.Set(key, strconv.FormatInt(val, 10))
			}
		case float64:
			if val != 0 {
				v.Set(key, strconv.FormatFloat(val, 'f', -1, 64))
			}
		case bool:
			v.Set(key, strconv.FormatBool(val))
		}
	}
	return v
}
