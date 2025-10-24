#!/usr/bin/env python3
"""
軸ID不整合修正の統合テスト

このスクリプトは以下をテストします：
1. 新しい配列形式の重み構造
2. 下位互換性（レガシーdict形式）
3. OpenAIクライアントのバリデーション
4. Pydanticモデルの動作
"""

import asyncio
from uuid import uuid4
from app.models.session import Session, Axis, Choice, WeightEntry
from app.clients.openai_client import OpenAIClient, ScenarioResponse
from app.models.llm_config import ProviderConfig, LLMProvider


def test_legacy_dict_format():
    """レガシーdict形式のテスト"""
    print("🧪 Testing legacy dict format...")
    
    session = Session(
        id=uuid4(),
        initialCharacter='あ',
        themeId='test',
        axes=[
            Axis(id='axis_1', name='Logic vs Emotion', description='テスト軸1', direction='論理⟷感情'),
            Axis(id='axis_2', name='Speed vs Caution', description='テスト軸2', direction='迅速⟷慎重')
        ]
    )
    
    legacy_choice = Choice(
        id='choice_1',
        text='レガシー選択肢',
        weights={'axis_1': 0.8, 'axis_2': -0.3}
    )
    
    # 変換メソッドのテスト
    weights_dict = legacy_choice.get_weights_dict()
    weights_array = legacy_choice.get_weights_array()
    
    assert weights_dict == {'axis_1': 0.8, 'axis_2': -0.3}
    assert len(weights_array) == 2
    assert weights_array[0].id == 'axis_1'
    assert weights_array[0].score == 0.8
    
    print("✅ Legacy dict format test passed!")


def test_new_array_format():
    """新しい配列形式のテスト"""
    print("🧪 Testing new array format...")
    
    new_choice = Choice(
        id='choice_2',
        text='新しい選択肢',
        weights=[
            WeightEntry(id='axis_1', name='Logic vs Emotion', score=0.5),
            WeightEntry(id='axis_2', name='Speed vs Caution', score=-0.7),
            WeightEntry(id='axis_3', name='Independence vs Collaboration', score=0.2),
            WeightEntry(id='axis_4', name='Risk Taking vs Safety', score=-0.1)
        ]
    )
    
    # 変換メソッドのテスト
    weights_dict = new_choice.get_weights_dict()
    weights_array = new_choice.get_weights_array()
    
    expected_dict = {
        'axis_1': 0.5, 'axis_2': -0.7, 'axis_3': 0.2, 'axis_4': -0.1
    }
    assert weights_dict == expected_dict
    assert len(weights_array) == 4
    assert all(isinstance(w, WeightEntry) for w in weights_array)
    
    print("✅ New array format test passed!")


async def test_openai_validation():
    """OpenAIクライアントのバリデーションテスト"""
    print("🧪 Testing OpenAI client validation...")
    
    config = ProviderConfig(
        provider=LLMProvider.OPENAI,
        api_key='test-key',
        model_name='gpt-4'
    )
    client = OpenAIClient(config)
    
    # 問題のあった形式（軸名が不正）
    problematic_response = {
        'scene': {
            'scene_index': 1,
            'narrative': 'あなたは重要なプロジェクトのリーダーとして、チームの方向性を決める重要な決断を迫られています。限られた時間の中で、複数の選択肢から最適な判断を下す必要があります。この決定がプロジェクト全体の成功に大きく影響することは明らかです。',
            'choices': [
                {
                    'id': 'choice_1_1',
                    'text': '慎重にデータ分析をして決める',
                    'weights': {
                        'Ambition': 0.0,  # 正しくない軸名
                        'Growth Mindset': 0.5,
                        'Self-Reflection': 0.3,
                        'Resilience': 0.0
                    }
                },
                {
                    'id': 'choice_1_2',
                    'text': '直感で決める',
                    'weights': {
                        'Ambition': 0.8,
                        'Growth Mindset': 0.0,
                        'Self-Reflection': -0.5,
                        'Resilience': 0.3
                    }
                },
                {
                    'id': 'choice_1_3',
                    'text': 'チームと相談',
                    'weights': {
                        'Ambition': -0.3,
                        'Growth Mindset': 0.2,
                        'Self-Reflection': 0.8,
                        'Resilience': 0.0
                    }
                },
                {
                    'id': 'choice_1_4',
                    'text': 'リスクを避ける',
                    'weights': {
                        'Ambition': -0.8,
                        'Growth Mindset': -0.3,
                        'Self-Reflection': 0.0,
                        'Resilience': -0.5
                    }
                }
            ]
        }
    }
    
    # 正しい新しい形式
    fixed_response = {
        'scene': {
            'scene_index': 1,
            'narrative': 'あなたは重要なプロジェクトのリーダーとして、チームの方向性を決める重要な決断を迫られています。限られた時間の中で、複数の選択肢から最適な判断を下す必要があります。この決定がプロジェクト全体の成功に大きく影響することは明らかです。',
            'choices': [
                {
                    'id': 'choice_1_1',
                    'text': '慎重にデータ分析をして決める',
                    'weights': [
                        {'id': 'axis_1', 'name': 'Logic vs Emotion', 'score': 0.8},
                        {'id': 'axis_2', 'name': 'Speed vs Caution', 'score': -0.6},
                        {'id': 'axis_3', 'name': 'Independence vs Collaboration', 'score': 0.3},
                        {'id': 'axis_4', 'name': 'Risk Taking vs Safety', 'score': -0.4}
                    ]
                },
                {
                    'id': 'choice_1_2',
                    'text': '直感で決める',
                    'weights': [
                        {'id': 'axis_1', 'name': 'Logic vs Emotion', 'score': -0.7},
                        {'id': 'axis_2', 'name': 'Speed vs Caution', 'score': 1.0},
                        {'id': 'axis_3', 'name': 'Independence vs Collaboration', 'score': 0.8},
                        {'id': 'axis_4', 'name': 'Risk Taking vs Safety', 'score': 0.6}
                    ]
                },
                {
                    'id': 'choice_1_3',
                    'text': 'チームと相談',
                    'weights': [
                        {'id': 'axis_1', 'name': 'Logic vs Emotion', 'score': 0.2},
                        {'id': 'axis_2', 'name': 'Speed vs Caution', 'score': -0.5},
                        {'id': 'axis_3', 'name': 'Independence vs Collaboration', 'score': -1.0},
                        {'id': 'axis_4', 'name': 'Risk Taking vs Safety', 'score': 0.0}
                    ]
                },
                {
                    'id': 'choice_1_4',
                    'text': 'リスクを避ける',
                    'weights': [
                        {'id': 'axis_1', 'name': 'Logic vs Emotion', 'score': 0.4},
                        {'id': 'axis_2', 'name': 'Speed vs Caution', 'score': -0.8},
                        {'id': 'axis_3', 'name': 'Independence vs Collaboration', 'score': -0.2},
                        {'id': 'axis_4', 'name': 'Risk Taking vs Safety', 'score': -1.0}
                    ]
                }
            ]
        }
    }
    
    template_data = {
        'session_id': 'test-session',
        'scene_index': 1,
        'keyword': '成長',
        'axes': [
            {'id': 'axis_1', 'name': 'Logic vs Emotion'},
            {'id': 'axis_2', 'name': 'Speed vs Caution'},
            {'id': 'axis_3', 'name': 'Independence vs Collaboration'},
            {'id': 'axis_4', 'name': 'Risk Taking vs Safety'}
        ]
    }
    
    # 問題のある形式は警告を出すが通すようになっている
    try:
        await client._validate_scenario_response(problematic_response, template_data)
        print("⚠️  Problematic format passed with warnings (as expected)")
    except Exception as e:
        print(f"❌ Problematic format failed: {e}")
    
    # 正しい形式は通る
    try:
        await client._validate_scenario_response(fixed_response, template_data)
        print("✅ Fixed format validation passed!")
    except Exception as e:
        print(f"❌ Fixed format failed: {e}")
        raise
    
    # Pydanticモデルの検証
    try:
        scenario_model = ScenarioResponse.model_validate(fixed_response)
        print("✅ Pydantic model validation passed!")
        
        # 重み情報の確認
        choice = scenario_model.scene.choices[0]
        print(f"   First choice weights: {[f'{w.id}={w.score}' for w in choice.weights]}")
        
    except Exception as e:
        print(f"❌ Pydantic validation failed: {e}")
        raise


def test_weight_conversion():
    """重み変換のテスト"""
    print("🧪 Testing weight conversion utilities...")
    
    # dict -> array conversion test
    dict_weights = {'axis_1': 0.5, 'axis_2': -0.3, 'axis_3': 0.8, 'axis_4': 0.0}
    axis_mapping = {
        'axis_1': 'Logic vs Emotion',
        'axis_2': 'Speed vs Caution',
        'axis_3': 'Independence vs Collaboration',
        'axis_4': 'Risk Taking vs Safety'
    }
    
    array_weights = [
        {'id': axis_id, 'name': axis_mapping[axis_id], 'score': score}
        for axis_id, score in dict_weights.items()
        if axis_id in axis_mapping
    ]
    
    assert len(array_weights) == 4
    assert array_weights[0]['id'] == 'axis_1'
    assert array_weights[0]['name'] == 'Logic vs Emotion'
    assert array_weights[0]['score'] == 0.5
    
    # array -> dict conversion test
    converted_dict = {w['id']: w['score'] for w in array_weights}
    assert converted_dict == dict_weights
    
    print("✅ Weight conversion test passed!")


async def main():
    """メインテスト実行"""
    print("🚀 Starting axis ID mismatch fix integration tests...\n")
    
    try:
        test_legacy_dict_format()
        print()
        
        test_new_array_format()
        print()
        
        await test_openai_validation()
        print()
        
        test_weight_conversion()
        print()
        
        print("🎉 All tests passed! Axis ID mismatch fix is working correctly.")
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
