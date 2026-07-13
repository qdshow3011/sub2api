"""Regression checks for the Docker Compose installation path."""

from pathlib import Path
import unittest


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

    def test_host_port_is_separate_from_container_port(self):
        for path in COMPOSE_FILES:
            text = path.read_text(encoding="utf-8")
            if '"${BIND_HOST' in text:
                self.assertIn("${HOST_PORT:-8080}:8080", text, path)
                self.assertNotIn("${SERVER_PORT:-8080}:8080", text, path)


    def test_deploy_script_validates_downloads_and_docker(self):
        text = (DEPLOY / "docker-deploy.sh").read_text(encoding="utf-8")
        self.assertIn("docker compose version", text)
        self.assertIn("curl -fsSL", text)
        self.assertTrue("--fail" in text or "curl -fsSL" in text)


if __name__ == "__main__":
    unittest.main()
