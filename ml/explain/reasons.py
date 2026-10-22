"""Human-readable explanations for quality predictions.

Converts raw feature values and model outputs into plain-language
explanations that help users understand why an image was rated
the way it was.
"""

from ml.features.extractor import FEATURE_ORDER


# Reference statistics from clean images (populated during training)
# These are median values from the pristine reference images
CLEAN_REFERENCE_STATS: dict[str, float] = {}


def set_reference_stats(stats: dict[str, float]) -> None:
    """Set reference statistics from clean training images."""
    global CLEAN_REFERENCE_STATS
    CLEAN_REFERENCE_STATS = stats


def explain_feature(name: str, value: float, ref_value: float | None = None) -> str | None:
    """Generate a human-readable explanation for a feature value.

    Compares the value against known thresholds or reference statistics
    to describe what the value means for image quality.

    Returns None if the value is in the normal range.
    """
    ref = ref_value or CLEAN_REFERENCE_STATS.get(name)

    explanations = {
        "laplacian_variance": _explain_sharpness,
        "tenengrad": _explain_tenengrad,
        "fft_high_freq_ratio": _explain_fft,
        "luminance_mean": _explain_brightness,
        "dark_clip_pct": _explain_dark_clip,
        "bright_clip_pct": _explain_bright_clip,
        "luminance_entropy": _explain_entropy,
        "dynamic_range": _explain_dynamic_range,
        "immerkaer_noise": _explain_noise,
        "wavelet_noise": _explain_wavelet_noise,
        "rms_contrast": _explain_contrast,
        "blockiness": _explain_blockiness,
        "colorfulness": _explain_colorfulness,
        "saturation_mean": _explain_saturation,
    }

    if name in explanations:
        return explanations[name](value, ref)
    return None


def _explain_sharpness(value: float, ref: float | None) -> str | None:
    if ref and value < ref * 0.3:
        return f"Laplacian variance {value:.1f}, well below the sharp-image median of {ref:.1f} — image appears significantly blurred"
    elif ref and value < ref * 0.6:
        return f"Laplacian variance {value:.1f} is below average ({ref:.1f}) — moderate loss of sharpness"
    return None


def _explain_tenengrad(value: float, ref: float | None) -> str | None:
    if ref and value < ref * 0.3:
        return f"Tenengrad gradient magnitude {value:.1f} is very low compared to sharp reference ({ref:.1f})"
    return None


def _explain_fft(value: float, ref: float | None) -> str | None:
    if ref and value < ref * 0.5:
        return f"High-frequency content ratio {value:.3f} indicates significant loss of fine detail"
    return None


def _explain_brightness(value: float, ref: float | None) -> str | None:
    if value < 50:
        return f"Mean luminance {value:.1f}/255 — image is very dark (underexposed)"
    elif value < 80:
        return f"Mean luminance {value:.1f}/255 — image appears underexposed"
    elif value > 220:
        return f"Mean luminance {value:.1f}/255 — image is very bright (overexposed)"
    elif value > 190:
        return f"Mean luminance {value:.1f}/255 — image appears overexposed"
    return None


def _explain_dark_clip(value: float, ref: float | None) -> str | None:
    if value > 0.3:
        return f"{value*100:.1f}% of pixels are near-black — significant shadow clipping"
    elif value > 0.1:
        return f"{value*100:.1f}% of pixels are near-black — some shadow detail lost"
    return None


def _explain_bright_clip(value: float, ref: float | None) -> str | None:
    if value > 0.3:
        return f"{value*100:.1f}% of pixels are near-white — significant highlight clipping"
    elif value > 0.1:
        return f"{value*100:.1f}% of pixels are near-white — some highlight detail lost"
    return None


def _explain_entropy(value: float, ref: float | None) -> str | None:
    if value < 5.0:
        return f"Luminance entropy {value:.2f} bits is low — limited tonal variation"
    return None


def _explain_dynamic_range(value: float, ref: float | None) -> str | None:
    if value < 100:
        return f"Dynamic range only {value:.0f}/255 — compressed tonal range (low contrast or exposure issue)"
    return None


def _explain_noise(value: float, ref: float | None) -> str | None:
    if ref and value > ref * 3:
        return f"Estimated noise σ={value:.2f}, significantly above clean reference ({ref:.2f})"
    elif value > 5.0:
        return f"Estimated noise σ={value:.2f} — noticeable noise present"
    return None


def _explain_wavelet_noise(value: float, ref: float | None) -> str | None:
    if ref and value > ref * 3:
        return f"Wavelet noise estimate {value:.2f} is elevated (clean median: {ref:.2f})"
    return None


def _explain_contrast(value: float, ref: float | None) -> str | None:
    if value < 20:
        return f"RMS contrast {value:.1f} is very low — image lacks tonal range"
    elif value < 35:
        return f"RMS contrast {value:.1f} — below average contrast"
    return None


def _explain_blockiness(value: float, ref: float | None) -> str | None:
    if value > 1.5:
        return f"Blockiness ratio {value:.2f} — visible block-boundary artifacts (JPEG compression)"
    elif value > 1.2:
        return f"Blockiness ratio {value:.2f} — mild compression artifacts detected"
    return None


def _explain_colorfulness(value: float, ref: float | None) -> str | None:
    if value < 10:
        return f"Colorfulness metric {value:.1f} — image appears nearly monochrome or desaturated"
    return None


def _explain_saturation(value: float, ref: float | None) -> str | None:
    if value < 20:
        return f"Mean saturation {value:.1f}/255 — colors are very muted"
    return None


def generate_explanations(features: dict[str, float],
                           issues: list[dict],
                           quality_score: float,
                           ref_stats: dict[str, float] | None = None) -> list[str]:
    """Generate a list of human-readable quality explanations.

    Args:
        features: Feature dict from the extractor.
        issues: Detected issues list.
        quality_score: Overall quality score.
        ref_stats: Optional reference statistics for comparison.

    Returns:
        List of explanation strings.
    """
    stats = ref_stats or CLEAN_REFERENCE_STATS
    explanations = []

    # Overall assessment
    if quality_score >= 80:
        explanations.append(f"Overall quality score {quality_score:.0f}/100 — good quality image")
    elif quality_score >= 50:
        explanations.append(f"Overall quality score {quality_score:.0f}/100 — image has some quality issues")
    else:
        explanations.append(f"Overall quality score {quality_score:.0f}/100 — significant quality problems detected")

    # Feature-specific explanations
    for name in FEATURE_ORDER:
        if name in features:
            explanation = explain_feature(name, features[name], stats.get(name))
            if explanation:
                explanations.append(explanation)

    # Issue summaries
    if not issues:
        explanations.append("No specific quality issues detected")
    else:
        for issue in issues:
            conf_pct = issue["confidence"] * 100
            explanations.append(
                f"Detected {issue['type'].replace('_', ' ')} "
                f"(severity: {issue['severity']}, confidence: {conf_pct:.0f}%)"
            )

    return explanations
