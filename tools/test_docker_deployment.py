"""Regression checks for the Docker Compose installation path."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"
COMPOSE_FILES = (
    DEPLOY / "docker-compose.yml",
    DEPLOY / "docker-compose.local.yml",
    DEPLOY / "docker-compose.dev.yml",
    DEPLOY / "docker-compose.standalone.yml",
)


class DockerDeploymentTests(unittest.TestCase):
    def test_compose_files_do_not_hardcode_container_names(self):
        for path in COMPOSE_FILES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("container_name:", text, path)

    def test_redis_password_is_expanded_inside_the_container(self):
        for path in COMPOSE_FILES:
            text = path.read_text(encoding="utf-8")
            if "redis-server" in text:
                self.assertIn("$${REDIS_PASSWORD", text, path)
                self.assertNotIn("${REDIS_PASSWORD:+", text, path)

    def test_compose_image_can_be_overridden(self):
        for path in COMPOSE_FILES:
            text = path.read_text(encoding="utf-8")
            if "image: weishaw/sub2api" in text:
                self.assertIn("${SUB2API_IMAGE:-", text, path)

    def test_compose_files_do_not_define_custom_networks(self):
        for path in COMPOSE_FILES:
            with path.open("r", encoding="utf-8") as handle:
                compose = yaml.safe_load(handle)
            self.assertNotIn("networks", compose, path)
            for service_name, service in compose["services"].items():
                self.assertNotIn("networks", service, f"{path}::{service_name}")

    def test_production_compose_does_not_publish_a_host_port(self):
        with (DEPLOY / "docker-compose.yml").open("r", encoding="utf-8") as handle:
            compose = yaml.safe_load(handle)
        service = compose["services"]["sub2api"]
        self.assertNotIn("ports", service)
        self.assertEqual(service.get("expose"), ["8080"])

    def test_local_compose_files_keep_host_port_mappings(self):
        for path in (
            DEPLOY / "docker-compose.local.yml",
            DEPLOY / "docker-compose.dev.yml",
            DEPLOY / "docker-compose.standalone.yml",
        ):
            with path.open("r", encoding="utf-8") as handle:
                compose = yaml.safe_load(handle)
            ports = compose["services"]["sub2api"].get("ports", [])
            self.assertTrue(ports, path)
            self.assertTrue(any(":8080" in port for port in ports), path)
            self.assertTrue(any("${HOST_PORT:-8080}" in port for port in ports), path)
            self.assertFalse(any("${SERVER_PORT:-8080}" in port for port in ports), path)

    def test_deploy_script_validates_downloads_and_docker(self):
        text = (DEPLOY / "docker-deploy.sh").read_text(encoding="utf-8")
        self.assertIn("docker compose version", text)
        self.assertIn("curl -fsSL", text)
        self.assertTrue("--fail" in text or "curl -fsSL" in text)

    def test_health_checks_use_curl_with_longer_start_period(self):
        for path in COMPOSE_FILES:
            with path.open("r", encoding="utf-8") as handle:
                compose = yaml.safe_load(handle)
            healthcheck = compose["services"]["sub2api"].get("healthcheck", {})
            self.assertEqual(healthcheck.get("test"), ["CMD", "curl", "-fsS", "http://localhost:8080/health"], path)
            self.assertEqual(healthcheck.get("start_period"), "60s", path)

        dockerfile = (DEPLOY / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3", dockerfile)
        self.assertIn('CMD curl -fsS "http://localhost:${SERVER_PORT:-8080}/health" >/dev/null || exit 1', dockerfile)

    def test_setup_migration_timeout_is_extended_for_docker_deployments(self):
        for path in COMPOSE_FILES:
            with path.open("r", encoding="utf-8") as handle:
                compose = yaml.safe_load(handle)
            env_items = compose["services"]["sub2api"]["environment"]
            self.assertIn("SETUP_MIGRATION_TIMEOUT_SECONDS=${SETUP_MIGRATION_TIMEOUT_SECONDS:-300}", env_items, path)


if __name__ == "__main__":
    unittest.main()
