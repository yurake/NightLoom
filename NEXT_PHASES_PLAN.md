# NightLoom MVP - Next Phases Implementation Plan
**Generated**: 2025-10-15
**Current Status**: User Story 1 (P1) ✅ COMPLETED

## 🎯 Current Achievement Summary

### ✅ Phase 1-3 Completed
- **Phase 1 (Setup)**: Project structure, dependencies, test frameworks
- **Phase 2 (Foundational)**: Core infrastructure, session management, LLM integration
- **Phase 3 (US1)**: Bootstrap + Keyword confirmation flow

### ✅ User Story 1 - 初回アクセスで診断を開始する (P1)
**Status**: 🏆 **FULLY IMPLEMENTED & TESTED**

**Completed Features**:
- ✅ Session bootstrap API (`/api/sessions/start`)
- ✅ Keyword confirmation API (`/api/sessions/{id}/keyword`)
- ✅ Frontend bootstrap flow with loading states
- ✅ Keyword selection UI (suggestions + custom input)
- ✅ First scene generation and display
- ✅ Theme application and session state management
- ✅ Comprehensive error handling and accessibility
- ✅ Contract tests, integration tests, E2E tests
- ✅ Performance requirements met (< 800ms bootstrap)

**Value Delivered**: ユーザーは NightLoom にアクセスして、初期キーワード候補から選択または独自入力により診断セッションを開始し、最初のシーンを表示できる。

---

## 🚀 Phase 4: User Story 2 Implementation

### Target: 4シーンの選択体験を完走する (Priority: P2)

**Goal**: ユーザーが各シーンで選択を行い、セッションステータス遷移とスコア集計が正しく進む

#### Phase 4A: Tests First (Fail First Strategy)
**Timeline**: 2-3 days

1. **Contract Tests** (T030-T033)
   - `backend/tests/api/test_scenes.py` - Scene retrieval API tests
   - `backend/tests/api/test_choices.py` - Choice submission API tests
   - `frontend/tests/integration/scenes.test.tsx` - Scene progression integration tests
   - `frontend/e2e/scenes.spec.ts` - 4-scene completion E2E tests

2. **Test Scenarios to Cover**:
   - Scene retrieval by index (1-4)
   - Choice submission and score recording
   - Session state transitions (PLAY → scene completion)
   - Progress tracking and navigation
   - Invalid scene access and error handling
   - Performance requirements (scene p95 ≤ 800ms)

#### Phase 4B: Backend Implementation
**Timeline**: 3-4 days

1. **API Endpoints** (T034-T036)
   - `GET /api/sessions/{sessionId}/scenes/{sceneIndex}` - Scene retrieval
   - `POST /api/sessions/{sessionId}/scenes/{sceneIndex}/choice` - Choice submission
   - Extend session service with scene navigation logic

2. **Service Extensions**:
   - Scene generation for indices 2-4
   - Choice recording and score accumulation
   - Session state validation and transitions
   - Progress tracking and completion detection

#### Phase 4C: Frontend Implementation 
**Timeline**: 4-5 days

1. **Components** (T037-T039)
   - `Scene.tsx` - Scene display with narrative and choices
   - `ChoiceOptions.tsx` - Choice selection UI with weights visualization
   - `ProgressIndicator.tsx` - Visual progress through 4 scenes

2. **Integration** (T040-T041)
   - Scene API integration with session context
   - Navigation between scenes after choice selection
   - Loading states and error handling for transitions
   - Progress persistence and resumption

**Phase 4 Completion Criteria**:
- All 4 scenes can be completed in sequence
- Choices are recorded and scored correctly
- Session progresses from INIT → PLAY → scene completion
- Independent testing passes for US2
- Performance targets met

---

## 🏁 Phase 5: User Story 3 Implementation

### Target: 結果と学びを受け取り次アクションへ進む (Priority: P3)

**Goal**: ユーザーが集計結果（評価軸・タイプ・キーワード）を理解し、再診断などの行動を選択できる

#### Phase 5A: Tests First
**Timeline**: 2-3 days

1. **Contract Tests** (T042-T044)
   - `backend/tests/api/test_results.py` - Result generation API tests
   - `frontend/tests/integration/results.test.tsx` - Result display integration
   - `frontend/e2e/results.spec.ts` - Complete diagnosis flow E2E

#### Phase 5B: Backend Implementation
**Timeline**: 3-4 days

1. **Result Generation** (T045-T046)
   - `POST /api/sessions/{sessionId}/result` - Result calculation endpoint
   - Integrate scoring and typing services
   - Type profile generation with fallback support
   - Result data formatting for frontend consumption

#### Phase 5C: Frontend Implementation
**Timeline**: 4-5 days

1. **Result Components** (T047-T050)
   - `result/page.tsx` - Result page layout
   - `ResultScreen.tsx` - Main result display component
   - `AxesScores.tsx` - Axis score visualization
   - `TypeCard.tsx` - Personality type display

2. **Actions** (T051-T052)
   - "もう一度診断する" restart functionality
   - Session cleanup and new session initiation
   - Result sharing capabilities (optional)

**Phase 5 Completion Criteria**:
- Complete 4-scene diagnosis generates meaningful results
- Axis scores and type profiles display correctly
- Result generation meets performance targets (p95 ≤ 1.2s)
- Restart functionality works end-to-end
- All user stories work independently and together

---

## 🎨 Phase 6: Polish & Cross-Cutting Concerns

### Target: Production-Ready Quality & Performance

**Timeline**: 5-7 days

#### Phase 6A: Observability & Monitoring (T053, T057)
- Comprehensive logging across all endpoints
- Performance monitoring and latency tracking
- Fallback scenario metrics and alerting
- Session completion rate tracking

#### Phase 6B: Accessibility & UX (T054, T056)
- ARIA labels and keyboard navigation
- Screen reader compatibility
- `prefers-reduced-motion` animation support
- Mobile responsive design (360px+ viewports)

#### Phase 6C: Testing & Quality (T058, T059)
- Expand unit test coverage to 90%+
- LLM failure simulation and fallback testing
- Performance optimization based on metrics
- Cross-browser compatibility testing

#### Phase 6D: Security & Reliability (T061, T062)
- Input validation and sanitization
- Rate limiting and session protection
- Code cleanup and refactoring
- Security audit and hardening

#### Phase 6E: Documentation & Deployment (T060, T063, T064)
- Update `docs/` and `README.md`
- Quickstart validation and setup instructions
- Deployment preparation and optimization
- Performance tuning for p95 requirements

---

## 📊 Implementation Strategy Options

### 🎯 Option A: Sequential MVP Delivery
**Recommended for single developer or small team**

1. **Week 1-2**: Complete Phase 4 (US2) fully
2. **Week 3-4**: Complete Phase 5 (US3) fully  
3. **Week 5**: Polish Phase 6 for production

**Benefits**:
- Each user story delivers independent value
- Can deploy and demo after each phase
- Lower risk, easier testing and validation

### ⚡ Option B: Parallel Feature Development
**For larger team with 3+ developers**

1. **Developer A**: Focus on Phase 4 (US2) 
2. **Developer B**: Focus on Phase 5 (US3)
3. **Developer C**: Focus on Phase 6 (Polish)
4. **Integration**: Merge and test all features together

**Benefits**:
- Faster overall completion
- Parallel testing and validation
- Earlier identification of integration issues

### 🚀 Option C: Incremental Enhancement
**For continuous delivery**

1. Deploy current US1 to production immediately
2. Add US2 incrementally with feature flags
3. Add US3 incrementally with feature flags
4. Polish and optimize continuously

**Benefits**:
- Immediate value delivery
- Real user feedback early
- Lower deployment risk

---

## 🎯 Next Immediate Actions

### Priority 1: Phase 4 Kickoff
1. **Create Failing Tests** for US2 scene progression
2. **Implement Scene API endpoints** following existing patterns
3. **Build Scene Navigation UI** components
4. **Integrate and Test** scene progression flow

### Priority 2: Project Tracking
1. **Update tasks.md** with current completion status
2. **Create Phase 4 milestone** tracking
3. **Document API contracts** for remaining endpoints
4. **Plan integration testing** strategy

### Priority 3: Quality Assurance
1. **Performance baseline** measurement for current US1
2. **Browser compatibility** testing
3. **Accessibility audit** of current implementation
4. **Security review** of session management

---

## 🏆 Success Metrics

### Technical Metrics
- **Performance**: Scene p95 ≤ 800ms, Result p95 ≤ 1.2s
- **Reliability**: 99% session completion rate
- **Test Coverage**: 90%+ unit tests, 100% E2E user story coverage
- **Accessibility**: WCAG 2.1 AA compliance

### Business Metrics  
- **User Engagement**: Complete diagnosis rate
- **User Experience**: Time to first scene < 2s
- **Error Rate**: < 1% session failures
- **Performance**: Support concurrent users efficiently

### Quality Gates
- All contract tests pass before implementation
- No regression in existing user stories
- Performance requirements met at each phase
- Independent user story testing passes

---

## 📞 Risk Mitigation

### Technical Risks
1. **LLM Service Reliability**: Robust fallback system already implemented
2. **Session State Management**: Comprehensive validation and error handling
3. **Frontend Performance**: Progressive loading and caching strategies
4. **Database Scaling**: In-memory design suitable for MVP scope

### Process Risks
1. **Scope Creep**: Strict adherence to MVP user stories only
2. **Integration Issues**: Fail First testing prevents late-stage problems  
3. **Performance Degradation**: Continuous monitoring and benchmarking
4. **User Experience**: Regular testing with E2E scenarios

---

## 💡 Future Enhancements (Post-MVP)

### Phase 7+: Advanced Features
- **Persistent Sessions**: Database integration for session storage
- **Advanced Analytics**: User behavior tracking and insights
- **Social Features**: Result sharing and community aspects
- **Personalization**: Adaptive questioning based on user patterns
- **Multiple Languages**: Internationalization and localization
- **Advanced AI**: Enhanced LLM integration with custom models

### Technical Improvements
- **Caching Layer**: Redis integration for improved performance
- **Real-time Features**: WebSocket integration for live diagnostics
- **Mobile Apps**: Native iOS/Android applications
- **API Versioning**: Support for multiple client versions
- **Advanced Security**: OAuth integration, user authentication

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-15  
**Next Review**: After Phase 4 completion  
**Maintainer**: Development Team
