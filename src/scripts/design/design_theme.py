#!/usr/bin/env python3
import sys
import os
import re
import argparse
import math
import difflib

# Canonical ordering of shadcn variables as defined in StratOS mapping-table
MAP_TABLE_ORDER = [
    '--background',
    '--foreground',
    '--card',
    '--card-foreground',
    '--popover',
    '--popover-foreground',
    '--primary',
    '--primary-foreground',
    '--secondary',
    '--secondary-foreground',
    '--muted',
    '--muted-foreground',
    '--accent',
    '--accent-foreground',
    '--destructive',
    '--destructive-foreground',
    '--border',
    '--input',
    '--ring'
]

def extract_frontmatter(content: str) -> str:
    """Extracts frontmatter lines from content, enforcing strict format constraints."""
    lines = content.splitlines()
    if not lines or lines[0].rstrip() != '---':
        raise ValueError("File must start with '---'")
    
    fm_lines = []
    found_end = False
    for line in lines[1:]:
        if line.rstrip() == '---':
            found_end = True
            break
        fm_lines.append(line)
        
    if not found_end:
        raise ValueError("Closing '---' not found")
        
    return '\n'.join(fm_lines)

def parse_yaml(fm_text: str) -> dict:
    """Parses standard key-value YAML frontmatter including nested structures using standard library only."""
    result = {}
    stack = [(-1, result)]  # stack of (indent, dict)
    
    for line in fm_text.splitlines():
        # Remove comments, respecting quotes
        in_quote = False
        quote_char = None
        comment_idx = -1
        for idx, char in enumerate(line):
            if char in ('"', "'"):
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif quote_char == char:
                    in_quote = False
            elif char == '#' and not in_quote:
                comment_idx = idx
                break
        
        if comment_idx != -1:
            line = line[:comment_idx]
            
        stripped = line.strip()
        if not stripped:
            continue
            
        indent = len(line) - len(line.lstrip())
        
        if ':' not in stripped:
            continue
            
        k, v = stripped.split(':', 1)
        k = k.strip()
        v = v.strip()
        
        # Clean quotes
        if (k.startswith('"') and k.endswith('"')) or (k.startswith("'") and k.endswith("'")):
            k = k[1:-1]
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
            
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
            
        parent = stack[-1][1]
        
        if v == '':
            new_dict = {}
            parent[k] = new_dict
            stack.append((indent, new_dict))
        else:
            if v.startswith('{') and v.endswith('}'):
                inner = v[1:-1].strip()
                new_dict = {}
                if inner:
                    pairs = inner.split(',')
                    for pair in pairs:
                        if ':' in pair:
                            pk, pv = pair.split(':', 1)
                            pk = pk.strip().strip('"').strip("'")
                            pv = pv.strip().strip('"').strip("'")
                            new_dict[pk] = pv
                parent[k] = new_dict
            elif v.lower() == 'true':
                parent[k] = True
            elif v.lower() == 'false':
                parent[k] = False
            elif v.lower() == 'null':
                parent[k] = None
            else:
                try:
                    if '.' in v:
                        parent[k] = float(v)
                    else:
                        parent[k] = int(v)
                except ValueError:
                    parent[k] = v
                    
    return result

def is_oklch(color_str: str) -> bool:
    """Returns True if the input string is an oklch(...) specification."""
    return bool(re.match(r'^oklch\(\s*[0-9.]+\s+[0-9.]+\s+[0-9.]+\s*\)$', color_str.strip()))

def parse_oklch_components(color_str: str):
    """Parses oklch components into (L, C, H)."""
    match = re.match(r'^oklch\(\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*\)$', color_str.strip())
    if match:
        return float(match.group(1)), float(match.group(2)), match.group(3)
    return None

def oklch_to_linear_srgb(l: float, c: float, h_deg: float):
    # 1. Convert hue to radians
    h_rad = math.radians(h_deg)
    
    # 2. Convert OKLCH to Oklab
    a = c * math.cos(h_rad)
    b = c * math.sin(h_rad)
    
    # 3. Convert Oklab to LMS
    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b
    
    # 4. Non-linear LMS to linear LMS
    l_lin = l_ ** 3
    m_lin = m_ ** 3
    s_lin = s_ ** 3
    
    # 5. LMS to linear sRGB
    r = +4.0767416621 * l_lin - 3.3077115913 * m_lin + 0.2309699292 * s_lin
    g = -1.2684380046 * l_lin + 2.6097574011 * m_lin - 0.3413193965 * s_lin
    b = -0.0041960863 * l_lin - 0.7034186147 * m_lin + 1.7076147010 * s_lin
    
    # 6. Clip to sRGB gamut [0.0, 1.0] for physical display representation
    r_clipped = max(0.0, min(1.0, r))
    g_clipped = max(0.0, min(1.0, g))
    b_clipped = max(0.0, min(1.0, b))
    
    return r_clipped, g_clipped, b_clipped

def get_relative_luminance(color_str: str) -> float:
    """Converts OKLCH to relative luminance Y."""
    components = parse_oklch_components(color_str)
    if not components:
        return 0.205  # Default fallback relative luminance
        
    L, C, H_str = components
    try:
        H = float(H_str)
    except ValueError:
        H = 0.0
        
    r, g, b = oklch_to_linear_srgb(L, C, H)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_contrast_ratio(color1: str, color2: str) -> float:
    """Calculates WCAG relative luminance contrast ratio."""
    y1 = get_relative_luminance(color1)
    y2 = get_relative_luminance(color2)
    lighter = max(y1, y2)
    darker = min(y1, y2)
    return (lighter + 0.05) / (darker + 0.05)

def convert_to_clamp(val) -> str:
    """Converts a pixel-based anchor to a fluid clamp configuration per DR-003."""
    if isinstance(val, str):
        val_str = val.strip()
        if val_str.endswith('px'):
            try:
                num = float(val_str[:-2])
            except ValueError:
                return val
        else:
            try:
                num = float(val_str)
            except ValueError:
                return val
    elif isinstance(val, (int, float)):
        num = float(val)
    else:
        return val

    if num >= 9999 or num < 16:
        return f"{int(num)}px" if num.is_integer() else f"{num}px"
        
    min_val = max(round(num * 0.66), 12)
    diff = num - min_val
    
    min_str = f"{int(min_val)}px"
    max_str = f"{int(num)}px"
    diff_str = f"{int(diff)}" if diff.is_integer() else f"{diff:.2f}"
    
    return f"clamp({min_str}, calc({min_str} + {diff_str} * ((100vw - 360px) / 920)), {max_str})"

def get_color_token(colors: dict, name: str, fallback_val: str, warnings: list) -> str:
    """Retrieves a color token, recording fallback warnings if missing."""
    if name in colors:
        return colors[name]
    warnings.append(f"/* design-theme: {name} missing, fell back to {fallback_val} */")
    return fallback_val

def derive_foreground(base_color: str, name: str, warnings: list) -> str:
    """Derives foreground color using WCAG relative luminance contrast maximization."""
    if not is_oklch(base_color):
        warnings.append(f"/* design-theme: non-oklch {name}; foreground defaulted */")
        return "oklch(0.205 0 0)"
    
    white = "oklch(0.985 0 0)"
    black = "oklch(0.205 0 0)"
    
    contrast_white = get_contrast_ratio(white, base_color)
    contrast_black = get_contrast_ratio(black, base_color)
    
    if contrast_white >= contrast_black:
        return white
    else:
        return black

def derive_muted_foreground(on_surface_color: str, warnings: list) -> str:
    """Derives light mode muted-foreground from on-surface as oklch(0.50 C H)."""
    if not is_oklch(on_surface_color):
        warnings.append("/* design-theme: non-oklch on-surface; muted-foreground defaulted */")
        return "oklch(0.50 0.0000 0)"
    components = parse_oklch_components(on_surface_color)
    if not components:
        return "oklch(0.50 0.0000 0)"
    _, C, H = components
    return f"oklch(0.50 {C:.4f} {H})"

def derive_dark_color(light_color: str, role: str, warnings: list) -> str:
    """Derives dark-mode equivalent for a given light-mode OKLCH color by role."""
    if not is_oklch(light_color):
        warnings.append(f"/* design-theme: non-oklch {role}; dark value defaulted to light value */")
        return light_color
        
    components = parse_oklch_components(light_color)
    if not components:
        return light_color
        
    L, C, H = components
    
    if role == 'background':
        return f"oklch(0.17 {min(C, 0.02):.4f} {H})"
    elif role == 'text':
        return f"oklch(0.96 {min(C, 0.02):.4f} {H})"
    elif role == 'muted-text':
        return f"oklch(0.70 {C:.4f} {H})"
    elif role == 'muted':
        return f"oklch(0.24 {min(C, 0.03):.4f} {H})"
    elif role == 'border':
        return f"oklch(0.27 {min(C, 0.03):.4f} {H})"
    elif role == 'accent':
        return f"oklch({min(L + 0.08, 0.85):.3f} {C * 0.92:.4f} {H})"
    elif role == 'destructive':
        return f"oklch({max(L, 0.55):.3f} {C:.4f} {H})"
    else:
        return light_color

def get_dark_var(name: str, colors_dark: dict, derived_val: str) -> str:
    """Resolves dark variable value prioritizing colorsDark overrides."""
    if name in colors_dark:
        return colors_dark[name]
    return derived_val

def generate_css(data: dict) -> tuple:
    """Generates the CSS variables structure based on parsed frontmatter data."""
    warnings = []
    colors = data.get('colors', {})
    colors_dark = data.get('colorsDark', {})
    rounded = data.get('rounded', {})
    typography = data.get('typography', {})
    spacing = data.get('spacing', {})
    
    # 1. Resolve light colors
    surface = get_color_token(colors, 'surface', 'oklch(0.985 0 0)', warnings)
    on_surface = get_color_token(colors, 'on-surface', 'oklch(0.205 0 0)', warnings)
    primary = get_color_token(colors, 'primary', 'oklch(0.205 0 0)', warnings)
    secondary = get_color_token(colors, 'secondary', 'oklch(0.554 0.046 257)', warnings)
    tertiary = get_color_token(colors, 'tertiary', 'oklch(0.55 0.15 35)', warnings)
    neutral = get_color_token(colors, 'neutral', 'oklch(0.985 0.005 80)', warnings)
    error = get_color_token(colors, 'error', 'oklch(0.577 0.228 27.3)', warnings)
    
    primary_fg = derive_foreground(primary, 'primary', warnings)
    secondary_fg = derive_foreground(secondary, 'secondary', warnings)
    accent_fg = derive_foreground(tertiary, 'tertiary', warnings)
    destructive_fg = derive_foreground(error, 'error', warnings)
    muted_fg_light = derive_muted_foreground(on_surface, warnings)
    
    light_vars = {
        '--background': surface,
        '--foreground': on_surface,
        '--card': surface,
        '--card-foreground': on_surface,
        '--popover': surface,
        '--popover-foreground': on_surface,
        '--primary': primary,
        '--primary-foreground': primary_fg,
        '--secondary': secondary,
        '--secondary-foreground': secondary_fg,
        '--muted': neutral,
        '--muted-foreground': muted_fg_light,
        '--accent': tertiary,
        '--accent-foreground': accent_fg,
        '--destructive': error,
        '--destructive-foreground': destructive_fg,
        '--border': neutral,
        '--input': neutral,
        '--ring': primary
    }
    
    # 2. Resolve dark colors with optional overrides
    dark_surface = get_dark_var('surface', colors_dark, derive_dark_color(surface, 'background', warnings))
    dark_on_surface = get_dark_var('on-surface', colors_dark, derive_dark_color(on_surface, 'text', warnings))
    dark_primary = get_dark_var('primary', colors_dark, derive_dark_color(primary, 'accent', warnings))
    dark_secondary = get_dark_var('secondary', colors_dark, derive_dark_color(secondary, 'accent', warnings))
    dark_tertiary = get_dark_var('tertiary', colors_dark, derive_dark_color(tertiary, 'accent', warnings))
    dark_error = get_dark_var('error', colors_dark, derive_dark_color(error, 'destructive', warnings))
    
    dark_primary_fg = derive_foreground(dark_primary, 'dark_primary', warnings)
    dark_secondary_fg = derive_foreground(dark_secondary, 'dark_secondary', warnings)
    dark_accent_fg = derive_foreground(dark_tertiary, 'dark_tertiary', warnings)
    dark_destructive_fg = derive_foreground(dark_error, 'dark_error', warnings)
    
    # Derivations from light source tokens
    derived_muted_dark = derive_dark_color(neutral, 'muted', warnings)
    derived_border_dark = derive_dark_color(neutral, 'border', warnings)
    derived_muted_fg_dark = derive_dark_color(on_surface, 'muted-text', warnings)
    
    # Overrides layered: specific override, then general override, then light derived value
    dark_muted = get_dark_var('muted', colors_dark, get_dark_var('neutral', colors_dark, derived_muted_dark))
    dark_border = get_dark_var('border', colors_dark, get_dark_var('neutral', colors_dark, derived_border_dark))
    dark_input = get_dark_var('input', colors_dark, get_dark_var('neutral', colors_dark, derived_border_dark))
    dark_muted_foreground = get_dark_var('muted-foreground', colors_dark, get_dark_var('on-surface', colors_dark, derived_muted_fg_dark))
    
    dark_vars = {
        '--background': dark_surface,
        '--foreground': dark_on_surface,
        '--card': dark_surface,
        '--card-foreground': dark_on_surface,
        '--popover': dark_surface,
        '--popover-foreground': dark_on_surface,
        '--primary': dark_primary,
        '--primary-foreground': dark_primary_fg,
        '--secondary': dark_secondary,
        '--secondary-foreground': dark_secondary_fg,
        '--muted': dark_muted,
        '--muted-foreground': dark_muted_foreground,
        '--accent': dark_tertiary,
        '--accent-foreground': dark_accent_fg,
        '--destructive': dark_error,
        '--destructive-foreground': dark_destructive_fg,
        '--border': dark_border,
        '--input': dark_input,
        '--ring': dark_primary
    }

    
    # 3. Perform dark mode WCAG AA checks
    contrast_pairs = [
        ('foreground', '--foreground', '--background'),
        ('card-foreground', '--card-foreground', '--card'),
        ('popover-foreground', '--popover-foreground', '--popover'),
        ('muted-foreground', '--muted-foreground', '--muted'),
        ('primary-foreground', '--primary-foreground', '--primary'),
        ('secondary-foreground', '--secondary-foreground', '--secondary'),
        ('accent-foreground', '--accent-foreground', '--accent'),
        ('destructive-foreground', '--destructive-foreground', '--destructive'),
    ]
    
    for token_name, fg_var, bg_var in contrast_pairs:
        fg_val = dark_vars[fg_var]
        bg_val = dark_vars[bg_var]
        ratio = get_contrast_ratio(fg_val, bg_val)
        if ratio < 4.5:
            warnings.append(f"/* design-theme: dark contrast {token_name} = {ratio:.1f}:1 below AA */")
            
    radius_val = rounded.get('md', '0.625rem')
    if isinstance(radius_val, (int, float)):
        radius_val = f"{radius_val}px"
        
    # Assemble output stylesheet content
    css_lines = []
    
    for w in warnings:
        css_lines.append(w)
        
    css_lines.append(":root {")
    css_lines.append(f"  --radius: {radius_val};")
    for k in MAP_TABLE_ORDER:
        if k in light_vars:
            css_lines.append(f"  {k}: {light_vars[k]};")
    css_lines.append("}")
    
    css_lines.append("")
    css_lines.append("@custom-variant dark (&:is(.dark *));")
    css_lines.append("")
    
    css_lines.append(".dark {")
    for k in MAP_TABLE_ORDER:
        if k in dark_vars:
            css_lines.append(f"  {k}: {dark_vars[k]};")
    css_lines.append("}")
    
    css_lines.append("")
    css_lines.append("@theme inline {")
    for k in MAP_TABLE_ORDER:
        if k in light_vars:
            css_name = k.replace('--', '--color-')
            css_lines.append(f"  {css_name}: var({k});")
            
    if 'sm' in rounded:
        sm_val = rounded['sm']
        sm_str = f"{sm_val}px" if isinstance(sm_val, (int, float)) else str(sm_val)
        css_lines.append(f"  --radius-sm: {sm_str};")
    else:
        css_lines.append("  --radius-sm: calc(var(--radius) - 4px);")
        
    css_lines.append("  --radius-md: var(--radius);")
    
    if 'lg' in rounded:
        lg_val = rounded['lg']
        lg_str = f"{lg_val}px" if isinstance(lg_val, (int, float)) else str(lg_val)
        css_lines.append(f"  --radius-lg: {lg_str};")
    else:
        css_lines.append("  --radius-lg: calc(var(--radius) + 4px);")
    
    for level, val in sorted(rounded.items()):
        if level not in ('sm', 'md', 'lg'):
            val_str = f"{val}px" if isinstance(val, (int, float)) else str(val)
            css_lines.append(f"  --radius-{level}: {val_str};")
            
    # Typography
    for level, level_data in sorted(typography.items()):
        if not isinstance(level_data, dict):
            continue
        font_family = level_data.get('fontFamily')
        font_size = level_data.get('fontSize')
        font_weight = level_data.get('fontWeight')
        line_height = level_data.get('lineHeight')
        letter_spacing = level_data.get('letterSpacing')
        
        if font_family:
            css_lines.append(f"  --font-{level}: {font_family};")
        if font_size is not None:
            css_lines.append(f"  --text-{level}: {convert_to_clamp(font_size)};")
        if font_weight is not None:
            css_lines.append(f"  --font-weight-{level}: {font_weight};")
        if line_height is not None:
            css_lines.append(f"  --leading-{level}: {line_height};")
        if letter_spacing is not None:
            css_lines.append(f"  --tracking-{level}: {letter_spacing};")
            
    # Spacing
    for level, val in sorted(spacing.items()):
        css_lines.append(f"  --spacing-{level}: {convert_to_clamp(val)};")
        
    css_lines.append("}")
    
    return "\n".join(css_lines) + "\n", warnings

def main():
    parser = argparse.ArgumentParser(description="Generate app CSS tokens from DESIGN.md frontmatter.")
    parser.add_argument('--design', required=True, help="Path to DESIGN.md file.")
    parser.add_argument('--out', help="Path to write the generated CSS theme file.")
    parser.add_argument('--check', help="Compare generated CSS with target file. Exit 0 if identical, exit 1 if different (prints unified diff).")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.design):
        print(f"Error: Design file '{args.design}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(args.design, 'r', encoding='utf-8') as f:
            content = f.read()
            
        fm_text = extract_frontmatter(content)
        data = parse_yaml(fm_text)
        
    except Exception as e:
        print(f"Error parsing design file: {e}", file=sys.stderr)
        sys.exit(1)
        
    css_out, warnings = generate_css(data)
    
    if args.check:
        if not os.path.exists(args.check):
            print(f"Check target file '{args.check}' does not exist.", file=sys.stderr)
            # Print entire diff as if target file was empty
            diff = difflib.unified_diff(
                [],
                css_out.splitlines(keepends=True),
                fromfile='empty',
                tofile=args.check
            )
            sys.stdout.writelines(diff)
            sys.exit(1)
            
        with open(args.check, 'r', encoding='utf-8') as f:
            target_content = f.read()
            
        # Enforce LF normalization on both ends for exact bytes check
        norm_css_out = css_out.replace('\r\n', '\n')
        norm_target_content = target_content.replace('\r\n', '\n')
        
        if norm_css_out == norm_target_content:
            sys.exit(0)
        else:
            diff = difflib.unified_diff(
                norm_target_content.splitlines(keepends=True),
                norm_css_out.splitlines(keepends=True),
                fromfile=args.check,
                tofile='generated'
            )
            print("Drift detected in generated tokens sheet:", file=sys.stderr)
            sys.stdout.writelines(diff)
            sys.exit(1)
            
    elif args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(css_out)
        sys.exit(0)
        
    else:
        # Print to stdout
        sys.stdout.write(css_out)
        sys.exit(0)

if __name__ == '__main__':
    main()
