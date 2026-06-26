import unittest
import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add design_theme path to sys.path so we can import it directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import design_theme

class TestDesignTheme(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).resolve().parent / 'fixtures'
        self.skycast_md = self.fixtures_dir / 'skycast.DESIGN.md'
        self.skycast_css = self.fixtures_dir / 'skycast.globals.css'
        
    def test_golden_file(self):
        with open(self.skycast_md, 'r', encoding='utf-8') as f:
            content = f.read()
        fm_text = design_theme.extract_frontmatter(content)
        data = design_theme.parse_yaml(fm_text)
        css_out, _ = design_theme.generate_css(data)
        
        with open(self.skycast_css, 'r', encoding='utf-8') as f:
            golden_content = f.read()
            
        self.assertEqual(css_out.replace('\r\n', '\n'), golden_content.replace('\r\n', '\n'))
        
    def test_idempotency(self):
        with open(self.skycast_md, 'r', encoding='utf-8') as f:
            content = f.read()
        fm_text = design_theme.extract_frontmatter(content)
        data = design_theme.parse_yaml(fm_text)
        css_out_1, _ = design_theme.generate_css(data)
        css_out_2, _ = design_theme.generate_css(data)
        self.assertEqual(css_out_1, css_out_2)
        
    def test_check_drift(self):
        # Write temporary CSS with drift
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_md = Path(tmpdir) / 'design.md'
            temp_css = Path(tmpdir) / 'theme.css'
            
            # Copy skycast_md to temp_md
            with open(self.skycast_md, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(temp_md, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
                
            # Run generator to write clean css
            script_path = Path(design_theme.__file__).resolve()
            subprocess.run([sys.executable, str(script_path), '--design', str(temp_md), '--out', str(temp_css)], check=True)
            
            # Check exit code 0 when identical
            res_0 = subprocess.run([sys.executable, str(script_path), '--design', str(temp_md), '--check', str(temp_css)], capture_output=True)
            self.assertEqual(res_0.returncode, 0)
            
            # Mutate one byte
            with open(temp_css, 'r', encoding='utf-8') as f:
                css_data = f.read()
            css_mutated = css_data.replace('--radius: 8px;', '--radius: 9px;')
            with open(temp_css, 'w', encoding='utf-8', newline='\n') as f:
                f.write(css_mutated)
                
            # Check exit code 1 when drift
            res_1 = subprocess.run([sys.executable, str(script_path), '--design', str(temp_md), '--check', str(temp_css)], capture_output=True, text=True)
            self.assertEqual(res_1.returncode, 1)
            self.assertIn('Drift detected', res_1.stderr)
            self.assertIn('-  --radius: 9px;', res_1.stdout)
            self.assertIn('+  --radius: 8px;', res_1.stdout)

    def test_missing_token_fallback(self):
        yaml_content = """---
type: design
colors:
  primary: "oklch(0.205 0 0)"
---
"""
        data = design_theme.parse_yaml(design_theme.extract_frontmatter(yaml_content))
        css_out, warnings = design_theme.generate_css(data)
        self.assertIn("/* design-theme: surface missing, fell back to oklch(0.985 0 0) */", css_out)
        self.assertIn("/* design-theme: on-surface missing, fell back to oklch(0.205 0 0) */", css_out)
        self.assertIn("--background: oklch(0.985 0 0);", css_out)
        self.assertIn("--foreground: oklch(0.205 0 0);", css_out)

    def test_leading_comment_rejection(self):
        yaml_content = """<!-- leading comment -->
---
type: design
---
"""
        with self.assertRaises(ValueError):
            design_theme.extract_frontmatter(yaml_content)

    def test_clamp_math(self):
        self.assertEqual(design_theme.convert_to_clamp('48px'), 'clamp(32px, calc(32px + 16 * ((100vw - 360px) / 920)), 48px)')
        self.assertEqual(design_theme.convert_to_clamp('16px'), 'clamp(12px, calc(12px + 4 * ((100vw - 360px) / 920)), 16px)')
        self.assertEqual(design_theme.convert_to_clamp('12px'), '12px')
        self.assertEqual(design_theme.convert_to_clamp('9999px'), '9999px')

    def test_dark_derive(self):
        yaml_content = """---
type: design
colors:
  surface: "oklch(0.985 0 0)"
  on-surface: "oklch(0.205 0 0)"
---
"""
        data = design_theme.parse_yaml(design_theme.extract_frontmatter(yaml_content))
        css_out, _ = design_theme.generate_css(data)
        self.assertIn(".dark {", css_out)
        self.assertIn("--background: oklch(0.17 0.0000 0);", css_out)
        self.assertIn("--foreground: oklch(0.96 0.0000 0);", css_out)

    def test_colors_dark_override(self):
        yaml_content = """---
type: design
colors:
  primary: "oklch(0.205 0 0)"
colorsDark:
  primary: "oklch(0.4 0.1 120)"
---
"""
        data = design_theme.parse_yaml(design_theme.extract_frontmatter(yaml_content))
        css_out, _ = design_theme.generate_css(data)
        # Primary in light mode is oklch(0.205 0 0)
        self.assertIn("--primary: oklch(0.205 0 0);", css_out.split(".dark {")[0])
        # Primary in dark mode is overridden verbatim
        self.assertIn("--primary: oklch(0.4 0.1 120);", css_out.split(".dark {")[1])

    def test_dark_contrast_warning(self):
        yaml_content = """---
type: design
colors:
  surface: "oklch(0.985 0 0)"
  on-surface: "oklch(0.205 0 0)"
colorsDark:
  surface: "oklch(0.17 0 0)"
  on-surface: "oklch(0.18 0 0)"
---
"""
        data = design_theme.parse_yaml(design_theme.extract_frontmatter(yaml_content))
        css_out, _ = design_theme.generate_css(data)
        # Should generate a dark contrast warning for foreground because surface and on-surface in dark mode will be too close
        self.assertIn("/* design-theme: dark contrast foreground", css_out)

if __name__ == '__main__':
    unittest.main()
