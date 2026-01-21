import unittest
from alpha_factory_v1.backend import genetic_tests as gt


class GeneticTestsTest(unittest.TestCase):
    def test_toy_optimal(self):
        genes = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 128}
        self.assertAlmostEqual(gt.toy_fitness(genes), 3.0, places=2)

    def test_stochastic_zero_noise(self):
        genes = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 128}
        self.assertAlmostEqual(
            gt.stochastic_fitness(genes, noise=0.0), gt.toy_fitness(genes), places=6
        )

    def test_missing_gene_raises(self):
        with self.assertRaises(KeyError):
            gt.toy_fitness({"temperature": 0.7})

    def test_geneconfig_roundtrip(self):
        cfg = gt.GeneConfig(0.8, 0.95, 256)
        d = cfg.as_dict()
        self.assertEqual(d["temperature"], 0.8)
        self.assertEqual(d["top_p"], 0.95)
        self.assertEqual(d["max_tokens"], 256)


if __name__ == "__main__":
    unittest.main()
