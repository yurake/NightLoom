"""
Tests for fallback keyword data integrity and quality.

Tests that fallback keywords match their expected initial characters
and meet quality requirements for the NightLoom diagnosis experience.
"""

import pytest
import jaconv
from typing import Dict

from app.services.fallback_assets import FallbackAssets


class TestFallbackKeywordIntegrity:
    """Test the integrity of fallback keyword data."""
    
    def get_first_hiragana_char(self, text: str) -> str:
        """
        Get the first hiragana character of a text.
        
        Uses the same logic as validate_fallback_keywords.py to ensure consistency.
        """
        # Convert katakana and full-width characters to hiragana
        hiragana_text = jaconv.kata2hira(jaconv.han2zen(text))
        
        # Common reading mappings for known words
        reading_map = {
            # あ行
            '愛情': 'あいじょう', '明るい': 'あかるい', '新しい': 'あたらしい', '温かい': 'あたたかい',
            
            # か行
            '希望': 'きぼう',  # Should be 'き' not 'か'
            '輝く': 'かがやく', '感謝': 'かんしゃ', '可愛い': 'かわいい', '活気': 'かっき',
            
            # さ行
            '爽やか': 'さわやか', '最高': 'さいこう', '咲く': 'さく', '才能': 'さいのう',
            '創造': 'そうぞう', '素晴らしい': 'すばらしい', '澄んだ': 'すんだ', '幸せ': 'しあわせ',
            
            # た行
            '楽しい': 'たのしい', '大切': 'たいせつ', '頼もしい': 'たのもしい', '確か': 'たしか',
            '力強い': 'ちからづよい',  # Should be 'ち' not 'た'
            '豊か': 'ゆたか',  # Should be 'ゆ' not 'た'
            
            # な行
            '懐かしい': 'なつかしい', '穏やか': 'おだやか', '自然': 'しぜん', '仲良し': 'なかよし',
            '内面': 'ないめん', '納得': 'なっとく',
            
            # は行
            '花咲く': 'はなさく', '春らしい': 'はるらしい', '晴れやか': 'はれやか', '美しい': 'うつくしい',
            '博愛': 'はくあい',
            
            # ま行
            '真心': 'まごころ', '眩しい': 'まぶしい', '満足': 'まんぞく', '学び': 'まなび',
            
            # や行
            '優しい': 'やさしい', '安らぎ': 'やすらぎ', '喜び': 'よろこび', '柔らか': 'やわらか',
            '約束': 'やくそく',
            
            # ら行
            '楽観的': 'らっかんてき', 'らしさ': 'らしさ', 'らくらく': 'らくらく', 'らんらん': 'らんらん',
            '立派': 'りっぱ', '理想': 'りそう', '凛とした': 'りんとした',
            
            # わ行
            '和やか': 'わやか', '笑顔': 'えがお', '輪になる': 'わになる', '若々しい': 'わかわかしい',
            '忘れない': 'わすれない'
        }
        
        if text in reading_map:
            return reading_map[text][0]  # Return first character
        
        # Fallback: try hiragana conversion
        hiragana = jaconv.kata2hira(text)
        return hiragana[0] if hiragana else text[0]
    
    @pytest.mark.parametrize("initial_char", [
        "あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"
    ])
    def test_keyword_initial_character_matches(self, initial_char: str):
        """Test that all keywords for each character start with the expected hiragana."""
        keywords = FallbackAssets.get_keyword_candidates(initial_char)
        
        assert len(keywords) > 0, f"No keywords found for character '{initial_char}'"
        
        mismatched_keywords = []
        
        for keyword in keywords:
            first_char = self.get_first_hiragana_char(keyword)
            if first_char != initial_char:
                mismatched_keywords.append((keyword, first_char))
        
        # Report all mismatches for better debugging
        if mismatched_keywords:
            mismatch_details = [
                f"'{keyword}' reads as '{actual}' (expected '{initial_char}')"
                for keyword, actual in mismatched_keywords
            ]
            pytest.fail(
                f"Keywords for '{initial_char}' have reading mismatches:\n" + 
                "\n".join(f"  - {detail}" for detail in mismatch_details)
            )
    
    def test_all_keywords_are_non_empty_strings(self):
        """Test that all fallback keywords are non-empty strings."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            for keyword in keywords:
                assert isinstance(keyword, str), f"Keyword '{keyword}' for '{char}' is not a string"
                assert len(keyword.strip()) > 0, f"Keyword for '{char}' is empty or whitespace-only"
    
    def test_keywords_are_reasonable_length(self):
        """Test that keywords are of reasonable length (2-8 characters typically)."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            for keyword in keywords:
                assert 1 <= len(keyword) <= 20, (
                    f"Keyword '{keyword}' for '{char}' has unusual length: {len(keyword)} characters"
                )
    
    def test_keywords_contain_japanese_characters(self):
        """Test that keywords contain Japanese characters (hiragana, katakana, or kanji)."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            for keyword in keywords:
                has_japanese = any(ord(character) > 127 for character in keyword)
                assert has_japanese, f"Keyword '{keyword}' for '{char}' should contain Japanese characters"
    
    def test_keywords_are_unique_within_character(self):
        """Test that keywords are unique within each character group."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            unique_keywords = set(keywords)
            assert len(keywords) == len(unique_keywords), (
                f"Duplicate keywords found for '{char}': {keywords}"
            )
    
    def test_expected_keyword_count_per_character(self):
        """Test that each character has the expected number of keywords (typically 4)."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            # Most characters should have exactly 4 keywords
            assert len(keywords) == 4, (
                f"Character '{char}' has {len(keywords)} keywords, expected 4: {keywords}"
            )
    
    def test_fallback_keywords_data_consistency(self):
        """Test overall data consistency across all characters."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        all_keywords = []
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            all_keywords.extend(keywords)
        
        # Check for unexpected duplicates across different characters
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        duplicates = {k: v for k, v in keyword_counts.items() if v > 1}
        
        # Some keywords might legitimately appear in multiple character groups
        # but we should be aware of them
        if duplicates:
            duplicate_list = [f"'{k}' appears {v} times" for k, v in duplicates.items()]
            # This is informational - not necessarily a failure
            print(f"Keywords appearing in multiple character groups: {', '.join(duplicate_list)}")


class TestFallbackKeywordQualityValidation:
    """Test quality validation aspects of fallback keywords."""
    
    def test_no_obviously_problematic_keywords(self):
        """Test that keywords don't contain obviously problematic content."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        # Keywords that would be problematic for a personality diagnosis
        problematic_patterns = [
            "死", "殺", "病", "痛", "悲", "恨", "憎", "怒",  # Negative/violent content
            "　",  # Full-width spaces
            " ",   # Leading/trailing spaces (should be trimmed)
        ]
        
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            for keyword in keywords:
                for pattern in problematic_patterns:
                    assert pattern not in keyword, (
                        f"Keyword '{keyword}' for '{char}' contains problematic pattern '{pattern}'"
                    )
    
    def test_keywords_suitable_for_personality_diagnosis(self):
        """Test that keywords are suitable for personality diagnosis context."""
        target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        # Verify keywords represent positive/neutral personality traits or concepts
        for char in target_chars:
            keywords = FallbackAssets.get_keyword_candidates(char)
            
            for keyword in keywords:
                # Keywords should not be single characters (too generic)
                assert len(keyword) >= 2, (
                    f"Keyword '{keyword}' for '{char}' is too short for meaningful personality diagnosis"
                )
                
                # Keywords should not be excessively long
                assert len(keyword) <= 8, (
                    f"Keyword '{keyword}' for '{char}' may be too long for display purposes"
                )
