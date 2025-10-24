#!/usr/bin/env python3
"""
簡単な軸ID不整合修正テスト
"""

from uuid import uuid4

def test_imports():
    """モジュールのインポートテスト"""
    try:
        from app.models.session import Session, Axis, Choice, WeightEntry
        print("✅ Session models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_new_choice_model():
    """新しいChoiceモデルのテスト"""
    try:
        from app.models.session import Choice, WeightEntry
        
        # 新しい配列形式でChoice作成
        choice = Choice(
            id='choice_1',
            text='テスト選択肢',
            weights=[
                WeightEntry(id='axis_1', name='Logic vs Emotion', score=0.5),
                WeightEntry(id='axis_2', name='Speed vs Caution', score=-0.3)
            ]
        )
        
        # 変換メソッドのテスト
        weights_dict = choice.get_weights_dict()
        weights_array = choice.get_weights_array()
        
        assert weights_dict == {'axis_1': 0.5, 'axis_2': -0.3}
        assert len(weights_array) == 2
        
        print("✅ New Choice model test passed")
        return True
    except Exception as e:
        print(f"❌ New Choice model test failed: {e}")
        return False

def test_legacy_choice_model():
    """レガシーChoiceモデルのテスト"""
    try:
        from app.models.session import Choice
        
        # レガシー辞書形式でChoice作成
        choice = Choice(
            id='choice_2',
            text='レガシー選択肢',
            weights={'axis_1': 0.8, 'axis_2': -0.6}
        )
        
        # 変換メソッドのテスト
        weights_dict = choice.get_weights_dict()
        weights_array = choice.get_weights_array()
        
        assert weights_dict == {'axis_1': 0.8, 'axis_2': -0.6}
        assert len(weights_array) == 2
        
        print("✅ Legacy Choice model test passed")
        return True
    except Exception as e:
        print(f"❌ Legacy Choice model test failed: {e}")
        return False

def test_openai_models():
    """OpenAIモデルのテスト"""
    try:
        from app.clients.openai_client import WeightEntry, ScenarioChoice, ScenarioResponse
        
        # WeightEntryのテスト
        weight = WeightEntry(id='axis_1', name='Logic vs Emotion', score=0.5)
        assert weight.id == 'axis_1'
        assert weight.score == 0.5
        
        print("✅ OpenAI models test passed")
        return True
    except Exception as e:
        print(f"❌ OpenAI models test failed: {e}")
        return False

def main():
    """メインテスト"""
    print("🚀 Starting simple axis ID fix tests...\n")
    
    tests_passed = 0
    total_tests = 4
    
    if test_imports():
        tests_passed += 1
    
    if test_new_choice_model(): 
        tests_passed += 1
        
    if test_legacy_choice_model():
        tests_passed += 1
        
    if test_openai_models():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Axis ID fix is working.")
    else:
        print("💥 Some tests failed.")
        exit(1)

if __name__ == '__main__':
    main()
