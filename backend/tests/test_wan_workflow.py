import json
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / "workflows" / "wan22_ti2v_5b_gguf_api.json"


class WanWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))

    def test_required_nodes_exist(self):
        expected = {
            "37": "UnetLoaderGGUF",
            "38": "CLIPLoader",
            "39": "VAELoader",
            "6": "CLIPTextEncode",
            "55": "Wan22ImageToVideoLatent",
            "3": "KSampler",
            "57": "CreateVideo",
            "58": "SaveVideo",
            "56": "LoadImage",
        }
        for node_id, class_type in expected.items():
            with self.subTest(node_id=node_id):
                self.assertEqual(self.workflow[node_id]["class_type"], class_type)

    def test_all_linked_node_references_exist(self):
        for node_id, node in self.workflow.items():
            for input_name, value in node.get("inputs", {}).items():
                if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str):
                    with self.subTest(node_id=node_id, input_name=input_name):
                        self.assertIn(value[0], self.workflow)

    def test_model_filename_matches_gguf_setup(self):
        self.assertEqual(
            self.workflow["37"]["inputs"]["unet_name"],
            "Wan2.2-TI2V-5B-Q4_K_M.gguf",
        )


if __name__ == "__main__":
    unittest.main()
