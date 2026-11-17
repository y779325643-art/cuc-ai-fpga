# JavaScript / MJS 函数与调用索引

使用当前 Node 内置 Acorn 解析全部 JS/MJS 源文件，不执行应用、幻灯片生成器或字符串模板。匿名回调以定义行标识；语法调用表达式不等于已验证运行路径。函数名的嵌套路径用于导航，不一定是可直接访问的 JavaScript 属性。

[返回总索引](README.md)。原始记录见 [js-symbols.json](js-symbols.json)。

## `app/app.js`

[打开源码](../../../../app/app.js)

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `taskDisplayName(taskType)` | [49](../../../../app/app.js#L49) | `taskRegistry.find` |
| `taskDisplayName.<anonymous@53>(task)` | [53](../../../../app/app.js#L53) | 无直接调用 |
| `generationMode()` | [56](../../../../app/app.js#L56) | `document.querySelector` |
| `showToast(message)` | [60](../../../../app/app.js#L60) | `elements.toast.classList.add`、`window.setTimeout` |
| `showToast.<anonymous@63>()` | [63](../../../../app/app.js#L63) | `elements.toast.classList.remove` |
| `applySample(taskType)` | [66](../../../../app/app.js#L66) | `genericSample`、`showToast`、`taskRegistry.find` |
| `applySample.<anonymous@68>(task)` | [68](../../../../app/app.js#L68) | 无直接调用 |
| `genericSample(taskType)` | [85](../../../../app/app.js#L85) | `<dynamic>.replace`、`normalized.replaceAll` |
| `statusClass(status)` | [95](../../../../app/app.js#L95) | `<dynamic>.includes`、`<dynamic>.some`、`<dynamic>.test`、`<dynamic>.toLowerCase`、`String` |
| `statusClass.<anonymous@98>(word)` | [98](../../../../app/app.js#L98) | `normalized.includes` |
| `renderStages(stages)` | [103](../../../../app/app.js#L103) | `<dynamic>.forEach`、`Object.entries` |
| `renderStages.<anonymous@105>([name, detail])` | [105](../../../../app/app.js#L105) | `document.createElement`、`elements.stageGrid.appendChild`、`item.append`、`statusClass` |
| `requestPayload()` | [118](../../../../app/app.js#L118) | `Number`、`elements.projectName.value.trim`、`elements.requirement.value.trim`、`engineeringContext`、`generationMode` |
| `engineeringContext()` | [130](../../../../app/app.js#L130) | `elements.clockMHz.value.trim`、`elements.ioSpec.value.trim`、`elements.targetPlatform.value.trim`、`elements.topModule.value.trim`、`selectedDeliverables` |
| `selectedDeliverables()` | [143](../../../../app/app.js#L143) | `<dynamic>.filter`、`<dynamic>.map`、`document.querySelector` |
| `selectedDeliverables.<anonymous@149>([, enabled])` | [149](../../../../app/app.js#L149) | 无直接调用 |
| `selectedDeliverables.<anonymous@149>([name])` | [149](../../../../app/app.js#L149) | 无直接调用 |
| `renderAmbiguityAudit(data)` | [152](../../../../app/app.js#L152) | `elements.taskType.querySelector`、`gaps.map`、`items.forEach`、`statusClass`、`taskDisplayName` |
| `renderAmbiguityAudit.<anonymous@180>(gap)` | [180](../../../../app/app.js#L180) | 无直接调用 |
| `renderAmbiguityAudit.<anonymous@183>(text)` | [183](../../../../app/app.js#L183) | `document.createElement`、`elements.ambiguityList.appendChild` |
| `readJsonResponse(response)` | [190](../../../../app/app.js#L190) | `JSON.parse`、`response.text` |
| `auditRequirement()` | [199](../../../../app/app.js#L199) | `JSON.stringify`、`fetch`、`new Error`、`readJsonResponse`、`renderAmbiguityAudit`、`requestPayload` |
| `showClarificationStop(audit)` | [219](../../../../app/app.js#L219) | `<dynamic>.join`、`<dynamic>.map`、`Object.fromEntries`、`renderStages`、`updateCounts` |
| `showClarificationStop.<anonymous@226>(question, index)` | [226](../../../../app/app.js#L226) | 无直接调用 |
| `showClarificationStop.<anonymous@230>(name)` | [230](../../../../app/app.js#L230) | 无直接调用 |
| `freeModeFiles(audit)` | [234](../../../../app/app.js#L234) | `<dynamic>.join`、`JSON.stringify`、`elements.topModule.value.trim`、`requestPayload` |
| `renderFreeHandoff(audit)` | [282](../../../../app/app.js#L282) | `<dynamic>.map`、`Object.fromEntries`、`freeModeFiles`、`renderFiles`、`renderStages`、`showToast`、`updateCounts` |
| `renderFreeHandoff.<anonymous@289>(name)` | [289](../../../../app/app.js#L289) | 无直接调用 |
| `selectFile(file)` | [294](../../../../app/app.js#L294) | `<dynamic>.forEach`、`elements.fileList.querySelectorAll` |
| `selectFile.<anonymous@297>(button)` | [297](../../../../app/app.js#L297) | `button.classList.toggle` |
| `renderFiles(files)` | [300](../../../../app/app.js#L300) | `files.find`、`files.forEach`、`selectFile` |
| `renderFiles.<anonymous@308>(file)` | [308](../../../../app/app.js#L308) | `button.addEventListener`、`button.append`、`document.createElement`、`elements.fileList.appendChild` |
| `renderFiles.<anonymous@308>.<anonymous@318>()` | [318](../../../../app/app.js#L318) | `selectFile` |
| `renderFiles.<anonymous@321>(file)` | [321](../../../../app/app.js#L321) | `file.path.startsWith` |
| `renderFiles.<anonymous@321>(file)` | [321](../../../../app/app.js#L321) | `file.path.startsWith` |
| `updateCounts(counts, total)` | [324](../../../../app/app.js#L324) | `document.querySelector` |
| `setBusy(busy)` | [331](../../../../app/app.js#L331) | `elements.button.classList.toggle`、`elements.button.querySelector`、`generationMode` |
| `updateModeUi()` | [341](../../../../app/app.js#L341) | `document.querySelector`、`elements.taskField.classList.toggle`、`generationMode`、`setBusy` |
| `checkBackend()` | [355](../../../../app/app.js#L355) | `fetch`、`new Error` |
| `loadTaskRegistry()` | [370](../../../../app/app.js#L370) | `Array.isArray`、`fetch`、`new Error`、`readJsonResponse`、`renderTaskRegistry`、`showToast` |
| `renderTaskRegistry(tasks, familyCount)` | [383](../../../../app/app.js#L383) | `document.createElement`、`elements.taskType.appendChild`、`elements.taskType.querySelector`、`tasks.forEach` |
| `renderTaskRegistry.<anonymous@392>(task)` | [392](../../../../app/app.js#L392) | `document.createElement`、`elements.taskType.appendChild` |
| `setAuditBusy(busy)` | [401](../../../../app/app.js#L401) | 无直接调用 |
| `<anonymous@406>(button)` | [406](../../../../app/app.js#L406) | `button.addEventListener` |
| `<anonymous@406>.<anonymous@407>()` | [407](../../../../app/app.js#L407) | `<dynamic>.classList.add`、`<dynamic>.forEach`、`button.classList.add`、`document.querySelector`、`document.querySelectorAll` |
| `<anonymous@406>.<anonymous@407>.<anonymous@408>(item)` | [408](../../../../app/app.js#L408) | `item.classList.remove` |
| `<anonymous@406>.<anonymous@407>.<anonymous@409>(view)` | [409](../../../../app/app.js#L409) | `view.classList.remove` |
| `<anonymous@415>()` | [415](../../../../app/app.js#L415) | `taskDisplayName` |
| `<anonymous@418>(input)` | [418](../../../../app/app.js#L418) | `input.addEventListener` |
| `<anonymous@421>()` | [421](../../../../app/app.js#L421) | `applySample`、`showToast` |
| `<anonymous@426>()` | [426](../../../../app/app.js#L426) | `auditRequirement`、`document.createElement`、`elements.ambiguityList.appendChild`、`setAuditBusy`、`showToast` |
| `<anonymous@446>(event)` | [446](../../../../app/app.js#L446) | `<dynamic>.forEach`、`<dynamic>.includes`、`JSON.stringify`、`auditRequirement`、`document.querySelectorAll`、`event.preventDefault`、`fetch`、`generationMode`、`new Error`、`readJsonResponse`、`renderFiles`、`renderFreeHandoff`、`renderStages`、`requestPayload`、`setBusy`、`showClarificationStop`、`showToast`、`statusClass`、`updateCounts` |
| `<anonymous@446>.<anonymous@452>(step)` | [452](../../../../app/app.js#L452) | `step.classList.add` |
| `<anonymous@446>.<anonymous@478>(step)` | [478](../../../../app/app.js#L478) | `step.classList.add`、`step.classList.remove` |
| `<anonymous@489>()` | [489](../../../../app/app.js#L489) | `navigator.clipboard.writeText`、`showToast` |
| `<anonymous@495>(name)` | [495](../../../../app/app.js#L495) | 无直接调用 |

模块级语法调用（含条件块，不等于一定发生）：`<dynamic>.addEventListener`、`<dynamic>.forEach`、`<dynamic>.map`、`Object.fromEntries`、`checkBackend`、`document.querySelector`、`document.querySelectorAll`、`elements.ambiguityButton.addEventListener`、`elements.form.addEventListener`、`elements.taskType.addEventListener`、`loadTaskRegistry`、`renderStages`、`updateModeUi`

## `outputs/presentations/project-overview-redesign/src/create_redesign_modules.mjs`

`outputs/presentations/project-overview-redesign/src/create_redesign_modules.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `main()` | 759 | `<dynamic>.join`、`<dynamic>.padStart`、`JSON.stringify`、`String`、`console.log`、`deckData.map`、`fs.mkdir`、`fs.writeFile`、`path.join` |
| `main.<anonymous@801>(slide, i)` | 801 | `<dynamic>.padStart`、`String` |
| `<anonymous@824>(error)` | 824 | `String`、`console.error`、`process.exit` |

模块级语法调用（含条件块，不等于一定发生）：`<dynamic>.catch`、`fileURLToPath`、`main`、`path.dirname`、`path.join`

## `outputs/presentations/project-overview-redesign/src/slides/project_deck_data.mjs`

`outputs/presentations/project-overview-redesign/src/slides/project_deck_data.mjs`

没有函数语法节点；模块数据或顶层生成动作请直接查看源码。

## `outputs/presentations/project-overview-redesign/src/slides/render_helpers.mjs`

`outputs/presentations/project-overview-redesign/src/slides/render_helpers.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `rect(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = "#8FA2B8", weight = 1.5)` | 43 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = "#8FA2B8")` | 54 | `Math.sign`、`line`、`rect` |
| `chip(slide, ctx, x, y, label, color = P.cyan)` | 60 | `rect`、`text` |
| `pattern(slide, ctx, dark = false)` | 65 | `line` |
| `footer(slide, ctx, n)` | 71 | `<dynamic>.padStart`、`String`、`line`、`text` |
| `frame(slide, ctx, data, n)` | 77 | `footer`、`pattern`、`rect`、`text` |
| `drawCover(slide, ctx, data)` | 88 | `data.metrics.forEach`、`pattern`、`rect`、`text` |
| `drawCover.<anonymous@99>(m, i)` | 99 | `rect`、`text` |
| `drawSection(slide, ctx, data, n)` | 108 | `<dynamic>.padStart`、`String`、`pattern`、`rect`、`text` |
| `drawCards(slide, ctx, data)` | 119 | `cards.forEach`、`noteBand` |
| `drawCards.<anonymous@121>(c, i)` | 121 | `Math.floor`、`rect`、`text` |
| `noteBand(slide, ctx, value, y = 586, color = P.cyan)` | 132 | `rect`、`text` |
| `drawTable(slide, ctx, data)` | 138 | `data.headers.forEach`、`data.rows.forEach`、`noteBand` |
| `drawTable.<anonymous@143>(h, i)` | 143 | `rect`、`text` |
| `drawTable.<anonymous@147>(row, r)` | 147 | `row.forEach` |
| `drawTable.<anonymous@147>.<anonymous@149>(cell, c)` | 149 | `rect`、`text` |
| `drawTimeline(slide, ctx, data)` | 157 | `data.stages.forEach`、`noteBand` |
| `drawTimeline.<anonymous@158>(s, i)` | 158 | `Math.floor`、`arrow`、`rect`、`text` |
| `drawCompare(slide, ctx, data)` | 172 | `data.left.forEach`、`data.right.forEach`、`noteBand`、`rect`、`text` |
| `drawCompare.<anonymous@180>(v, i)` | 180 | `bullet` |
| `drawCompare.<anonymous@181>(v, i)` | 181 | `bullet` |
| `bullet(slide, ctx, x, y, value, color = P.cyan)` | 185 | `rect`、`text` |
| `drawFlow(slide, ctx, data)` | 190 | `Math.min`、`data.steps.forEach`、`noteBand` |
| `drawFlow.<anonymous@192>(s, i)` | 192 | `arrow`、`rect`、`text` |
| `drawArchitecture(slide, ctx, data)` | 205 | `data.lanes.forEach`、`noteBand`、`rect`、`text` |
| `drawArchitecture.<anonymous@206>(l, i)` | 206 | `arrow`、`rect`、`text` |
| `drawDefinition(slide, ctx, data)` | 219 | `data.choices.forEach`、`rect`、`text` |
| `drawDefinition.<anonymous@222>(row, i)` | 222 | `line`、`text` |
| `drawConcepts(slide, ctx, data)` | 232 | `data.concepts.forEach` |
| `drawConcepts.<anonymous@233>(c, i)` | 233 | `Math.floor`、`rect`、`text` |
| `drawPipeline(slide, ctx, data)` | 243 | `data.steps.forEach`、`noteBand` |
| `drawPipeline.<anonymous@244>(s, i)` | 244 | `arrow`、`rect`、`text` |
| `drawSplitList(slide, ctx, data)` | 255 | `areas.forEach`、`noteBand` |
| `drawSplitList.<anonymous@257>([x, y, title, items, color])` | 257 | `items.forEach`、`rect`、`text` |
| `drawSplitList.<anonymous@257>.<anonymous@261>(item, i)` | 261 | `bullet` |
| `drawFeedback(slide, ctx, data)` | 266 | `data.mappings.forEach`、`noteBand` |
| `drawFeedback.<anonymous@267>(m, i)` | 267 | `arrow`、`rect`、`text` |
| `drawCodePair(slide, ctx, data)` | 281 | `noteBand`、`panels.forEach` |
| `drawCodePair.<anonymous@283>([x, title, rows], idx)` | 283 | `rect`、`rows.forEach`、`text` |
| `drawCodePair.<anonymous@283>.<anonymous@287>(r, i)` | 287 | `text` |
| `drawRoadmap(slide, ctx, data)` | 294 | `data.phases.forEach`、`noteBand` |
| `drawRoadmap.<anonymous@295>(p, i)` | 295 | `p[<computed>].forEach`、`rect`、`text` |
| `drawRoadmap.<anonymous@295>.<anonymous@300>(item, j)` | 300 | `bullet` |
| `drawRecap(slide, ctx, data)` | 305 | `chip`、`data.chapters.forEach`、`data.sentences.forEach` |
| `drawRecap.<anonymous@306>(s, i)` | 306 | `rect`、`text` |
| `drawRecap.<anonymous@313>(c, i)` | 313 | `<dynamic>.padStart`、`Math.floor`、`String`、`text` |
| `drawGlossary(slide, ctx, data)` | 318 | `data.concepts.forEach`、`text` |
| `drawGlossary.<anonymous@319>(c, i)` | 319 | `Math.floor`、`rect`、`text` |
| `renderSlide(presentation, ctx, data, n)` | 329 | `drawArchitecture`、`drawCards`、`drawCodePair`、`drawCompare`、`drawConcepts`、`drawCover`、`drawDefinition`、`drawFeedback`、`drawFlow`、`drawGlossary`、`drawPipeline`、`drawRecap`、`drawRoadmap`、`drawSection`、`drawSplitList`、`drawTable`、`drawTimeline`、`frame`、`presentation.slides.add` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-01.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-01.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide01(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-02.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-02.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide02(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-03.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-03.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide03(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-04.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-04.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide04(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-05.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-05.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide05(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-06.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-06.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide06(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-07.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-07.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide07(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-08.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-08.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide08(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-09.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-09.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide09(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-10.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-10.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide10(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-11.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-11.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide11(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-12.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-12.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide12(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-13.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-13.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide13(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-14.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-14.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide14(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-15.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-15.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide15(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-16.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-16.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide16(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-17.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-17.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide17(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-18.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-18.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide18(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-19.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-19.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide19(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-20.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-20.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide20(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-21.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-21.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide21(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-22.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-22.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide22(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-23.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-23.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide23(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-24.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-24.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide24(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-25.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-25.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide25(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-26.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-26.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide26(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-27.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-27.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide27(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-28.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-28.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide28(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-29.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-29.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide29(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-30.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-30.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide30(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-31.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-31.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide31(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-32.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-32.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide32(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-33.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-33.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide33(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-34.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-34.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide34(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-35.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-35.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide35(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-36.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-36.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide36(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/project-overview-redesign/src/slides/slide-37.mjs`

`outputs/presentations/project-overview-redesign/src/slides/slide-37.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `slide37(presentation, ctx)` | 4 | `renderSlide` |

## `outputs/presentations/team-sync-redesign/src/create_redesign_slide_modules.mjs`

`outputs/presentations/team-sync-redesign/src/create_redesign_slide_modules.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `loadDeckData()` | 9 | `<dynamic>`、`<dynamic>.replace`、`Function`、`fs.readFile`、`new Error`、`source.indexOf`、`source.slice` |
| `makeSlideSource(slide, index)` | 127 | `<dynamic>.padStart`、`JSON.stringify`、`String` |
| `main()` | 302 | `<dynamic>.padStart`、`String`、`fs.mkdir`、`fs.writeFile`、`loadDeckData`、`makeSlideSource`、`path.join` |

模块级语法调用（含条件块，不等于一定发生）：`fileURLToPath`、`main`、`path.dirname`、`path.join`、`path.resolve`

## `outputs/presentations/team-sync-redesign/src/slides/slide-01.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-01.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide01(presentation, ctx)` | 134 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide01.<anonymous@150>(m, i)` | 150 | `miniMetric` |
| `slide01.<anonymous@158>(p, i)` | 158 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide01.<anonymous@171>(l, i)` | 171 | `arrow`、`box`、`text` |
| `slide01.<anonymous@183>(s, i)` | 183 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide01.<anonymous@199>(g, i)` | 199 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide01.<anonymous@199>.<anonymous@204>(item, j)` | 204 | `ctx.addShape`、`text` |
| `slide01.<anonymous@213>(c, i)` | 213 | `Math.floor`、`box`、`text` |
| `slide01.<anonymous@222>(row, i)` | 222 | `text` |
| `slide01.<anonymous@226>(c, i)` | 226 | `Math.floor`、`box`、`text` |
| `slide01.<anonymous@234>(e, i)` | 234 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide01.<anonymous@243>(b, i)` | 243 | `Math.max`、`ctx.addShape`、`text` |
| `slide01.<anonymous@251>(c, i)` | 251 | `proofBand` |
| `slide01.<anonymous@255>(t, i)` | 255 | `Math.floor`、`box`、`text` |
| `slide01.<anonymous@266>(l, i)` | 266 | `arrow`、`box`、`text` |
| `slide01.<anonymous@275>(d, i)` | 275 | `text` |
| `slide01.<anonymous@279>(r, i)` | 279 | `box`、`text` |
| `slide01.<anonymous@288>(r, i)` | 288 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-02.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-02.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide02(presentation, ctx)` | 131 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide02.<anonymous@147>(m, i)` | 147 | `miniMetric` |
| `slide02.<anonymous@155>(p, i)` | 155 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide02.<anonymous@168>(l, i)` | 168 | `arrow`、`box`、`text` |
| `slide02.<anonymous@180>(s, i)` | 180 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide02.<anonymous@196>(g, i)` | 196 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide02.<anonymous@196>.<anonymous@201>(item, j)` | 201 | `ctx.addShape`、`text` |
| `slide02.<anonymous@210>(c, i)` | 210 | `Math.floor`、`box`、`text` |
| `slide02.<anonymous@219>(row, i)` | 219 | `text` |
| `slide02.<anonymous@223>(c, i)` | 223 | `Math.floor`、`box`、`text` |
| `slide02.<anonymous@231>(e, i)` | 231 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide02.<anonymous@240>(b, i)` | 240 | `Math.max`、`ctx.addShape`、`text` |
| `slide02.<anonymous@248>(c, i)` | 248 | `proofBand` |
| `slide02.<anonymous@252>(t, i)` | 252 | `Math.floor`、`box`、`text` |
| `slide02.<anonymous@263>(l, i)` | 263 | `arrow`、`box`、`text` |
| `slide02.<anonymous@272>(d, i)` | 272 | `text` |
| `slide02.<anonymous@276>(r, i)` | 276 | `box`、`text` |
| `slide02.<anonymous@285>(r, i)` | 285 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-03.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-03.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide03(presentation, ctx)` | 150 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide03.<anonymous@166>(m, i)` | 166 | `miniMetric` |
| `slide03.<anonymous@174>(p, i)` | 174 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide03.<anonymous@187>(l, i)` | 187 | `arrow`、`box`、`text` |
| `slide03.<anonymous@199>(s, i)` | 199 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide03.<anonymous@215>(g, i)` | 215 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide03.<anonymous@215>.<anonymous@220>(item, j)` | 220 | `ctx.addShape`、`text` |
| `slide03.<anonymous@229>(c, i)` | 229 | `Math.floor`、`box`、`text` |
| `slide03.<anonymous@238>(row, i)` | 238 | `text` |
| `slide03.<anonymous@242>(c, i)` | 242 | `Math.floor`、`box`、`text` |
| `slide03.<anonymous@250>(e, i)` | 250 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide03.<anonymous@259>(b, i)` | 259 | `Math.max`、`ctx.addShape`、`text` |
| `slide03.<anonymous@267>(c, i)` | 267 | `proofBand` |
| `slide03.<anonymous@271>(t, i)` | 271 | `Math.floor`、`box`、`text` |
| `slide03.<anonymous@282>(l, i)` | 282 | `arrow`、`box`、`text` |
| `slide03.<anonymous@291>(d, i)` | 291 | `text` |
| `slide03.<anonymous@295>(r, i)` | 295 | `box`、`text` |
| `slide03.<anonymous@304>(r, i)` | 304 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-04.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-04.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide04(presentation, ctx)` | 147 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide04.<anonymous@163>(m, i)` | 163 | `miniMetric` |
| `slide04.<anonymous@171>(p, i)` | 171 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide04.<anonymous@184>(l, i)` | 184 | `arrow`、`box`、`text` |
| `slide04.<anonymous@196>(s, i)` | 196 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide04.<anonymous@212>(g, i)` | 212 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide04.<anonymous@212>.<anonymous@217>(item, j)` | 217 | `ctx.addShape`、`text` |
| `slide04.<anonymous@226>(c, i)` | 226 | `Math.floor`、`box`、`text` |
| `slide04.<anonymous@235>(row, i)` | 235 | `text` |
| `slide04.<anonymous@239>(c, i)` | 239 | `Math.floor`、`box`、`text` |
| `slide04.<anonymous@247>(e, i)` | 247 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide04.<anonymous@256>(b, i)` | 256 | `Math.max`、`ctx.addShape`、`text` |
| `slide04.<anonymous@264>(c, i)` | 264 | `proofBand` |
| `slide04.<anonymous@268>(t, i)` | 268 | `Math.floor`、`box`、`text` |
| `slide04.<anonymous@279>(l, i)` | 279 | `arrow`、`box`、`text` |
| `slide04.<anonymous@288>(d, i)` | 288 | `text` |
| `slide04.<anonymous@292>(r, i)` | 292 | `box`、`text` |
| `slide04.<anonymous@301>(r, i)` | 301 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-05.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-05.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide05(presentation, ctx)` | 140 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide05.<anonymous@156>(m, i)` | 156 | `miniMetric` |
| `slide05.<anonymous@164>(p, i)` | 164 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide05.<anonymous@177>(l, i)` | 177 | `arrow`、`box`、`text` |
| `slide05.<anonymous@189>(s, i)` | 189 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide05.<anonymous@205>(g, i)` | 205 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide05.<anonymous@205>.<anonymous@210>(item, j)` | 210 | `ctx.addShape`、`text` |
| `slide05.<anonymous@219>(c, i)` | 219 | `Math.floor`、`box`、`text` |
| `slide05.<anonymous@228>(row, i)` | 228 | `text` |
| `slide05.<anonymous@232>(c, i)` | 232 | `Math.floor`、`box`、`text` |
| `slide05.<anonymous@240>(e, i)` | 240 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide05.<anonymous@249>(b, i)` | 249 | `Math.max`、`ctx.addShape`、`text` |
| `slide05.<anonymous@257>(c, i)` | 257 | `proofBand` |
| `slide05.<anonymous@261>(t, i)` | 261 | `Math.floor`、`box`、`text` |
| `slide05.<anonymous@272>(l, i)` | 272 | `arrow`、`box`、`text` |
| `slide05.<anonymous@281>(d, i)` | 281 | `text` |
| `slide05.<anonymous@285>(r, i)` | 285 | `box`、`text` |
| `slide05.<anonymous@294>(r, i)` | 294 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-06.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-06.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide06(presentation, ctx)` | 140 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide06.<anonymous@156>(m, i)` | 156 | `miniMetric` |
| `slide06.<anonymous@164>(p, i)` | 164 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide06.<anonymous@177>(l, i)` | 177 | `arrow`、`box`、`text` |
| `slide06.<anonymous@189>(s, i)` | 189 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide06.<anonymous@205>(g, i)` | 205 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide06.<anonymous@205>.<anonymous@210>(item, j)` | 210 | `ctx.addShape`、`text` |
| `slide06.<anonymous@219>(c, i)` | 219 | `Math.floor`、`box`、`text` |
| `slide06.<anonymous@228>(row, i)` | 228 | `text` |
| `slide06.<anonymous@232>(c, i)` | 232 | `Math.floor`、`box`、`text` |
| `slide06.<anonymous@240>(e, i)` | 240 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide06.<anonymous@249>(b, i)` | 249 | `Math.max`、`ctx.addShape`、`text` |
| `slide06.<anonymous@257>(c, i)` | 257 | `proofBand` |
| `slide06.<anonymous@261>(t, i)` | 261 | `Math.floor`、`box`、`text` |
| `slide06.<anonymous@272>(l, i)` | 272 | `arrow`、`box`、`text` |
| `slide06.<anonymous@281>(d, i)` | 281 | `text` |
| `slide06.<anonymous@285>(r, i)` | 285 | `box`、`text` |
| `slide06.<anonymous@294>(r, i)` | 294 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-07.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-07.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide07(presentation, ctx)` | 149 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide07.<anonymous@165>(m, i)` | 165 | `miniMetric` |
| `slide07.<anonymous@173>(p, i)` | 173 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide07.<anonymous@186>(l, i)` | 186 | `arrow`、`box`、`text` |
| `slide07.<anonymous@198>(s, i)` | 198 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide07.<anonymous@214>(g, i)` | 214 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide07.<anonymous@214>.<anonymous@219>(item, j)` | 219 | `ctx.addShape`、`text` |
| `slide07.<anonymous@228>(c, i)` | 228 | `Math.floor`、`box`、`text` |
| `slide07.<anonymous@237>(row, i)` | 237 | `text` |
| `slide07.<anonymous@241>(c, i)` | 241 | `Math.floor`、`box`、`text` |
| `slide07.<anonymous@249>(e, i)` | 249 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide07.<anonymous@258>(b, i)` | 258 | `Math.max`、`ctx.addShape`、`text` |
| `slide07.<anonymous@266>(c, i)` | 266 | `proofBand` |
| `slide07.<anonymous@270>(t, i)` | 270 | `Math.floor`、`box`、`text` |
| `slide07.<anonymous@281>(l, i)` | 281 | `arrow`、`box`、`text` |
| `slide07.<anonymous@290>(d, i)` | 290 | `text` |
| `slide07.<anonymous@294>(r, i)` | 294 | `box`、`text` |
| `slide07.<anonymous@303>(r, i)` | 303 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-08.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-08.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide08(presentation, ctx)` | 140 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide08.<anonymous@156>(m, i)` | 156 | `miniMetric` |
| `slide08.<anonymous@164>(p, i)` | 164 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide08.<anonymous@177>(l, i)` | 177 | `arrow`、`box`、`text` |
| `slide08.<anonymous@189>(s, i)` | 189 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide08.<anonymous@205>(g, i)` | 205 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide08.<anonymous@205>.<anonymous@210>(item, j)` | 210 | `ctx.addShape`、`text` |
| `slide08.<anonymous@219>(c, i)` | 219 | `Math.floor`、`box`、`text` |
| `slide08.<anonymous@228>(row, i)` | 228 | `text` |
| `slide08.<anonymous@232>(c, i)` | 232 | `Math.floor`、`box`、`text` |
| `slide08.<anonymous@240>(e, i)` | 240 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide08.<anonymous@249>(b, i)` | 249 | `Math.max`、`ctx.addShape`、`text` |
| `slide08.<anonymous@257>(c, i)` | 257 | `proofBand` |
| `slide08.<anonymous@261>(t, i)` | 261 | `Math.floor`、`box`、`text` |
| `slide08.<anonymous@272>(l, i)` | 272 | `arrow`、`box`、`text` |
| `slide08.<anonymous@281>(d, i)` | 281 | `text` |
| `slide08.<anonymous@285>(r, i)` | 285 | `box`、`text` |
| `slide08.<anonymous@294>(r, i)` | 294 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-09.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-09.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide09(presentation, ctx)` | 132 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide09.<anonymous@148>(m, i)` | 148 | `miniMetric` |
| `slide09.<anonymous@156>(p, i)` | 156 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide09.<anonymous@169>(l, i)` | 169 | `arrow`、`box`、`text` |
| `slide09.<anonymous@181>(s, i)` | 181 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide09.<anonymous@197>(g, i)` | 197 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide09.<anonymous@197>.<anonymous@202>(item, j)` | 202 | `ctx.addShape`、`text` |
| `slide09.<anonymous@211>(c, i)` | 211 | `Math.floor`、`box`、`text` |
| `slide09.<anonymous@220>(row, i)` | 220 | `text` |
| `slide09.<anonymous@224>(c, i)` | 224 | `Math.floor`、`box`、`text` |
| `slide09.<anonymous@232>(e, i)` | 232 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide09.<anonymous@241>(b, i)` | 241 | `Math.max`、`ctx.addShape`、`text` |
| `slide09.<anonymous@249>(c, i)` | 249 | `proofBand` |
| `slide09.<anonymous@253>(t, i)` | 253 | `Math.floor`、`box`、`text` |
| `slide09.<anonymous@264>(l, i)` | 264 | `arrow`、`box`、`text` |
| `slide09.<anonymous@273>(d, i)` | 273 | `text` |
| `slide09.<anonymous@277>(r, i)` | 277 | `box`、`text` |
| `slide09.<anonymous@286>(r, i)` | 286 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-10.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-10.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide10(presentation, ctx)` | 136 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide10.<anonymous@152>(m, i)` | 152 | `miniMetric` |
| `slide10.<anonymous@160>(p, i)` | 160 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide10.<anonymous@173>(l, i)` | 173 | `arrow`、`box`、`text` |
| `slide10.<anonymous@185>(s, i)` | 185 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide10.<anonymous@201>(g, i)` | 201 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide10.<anonymous@201>.<anonymous@206>(item, j)` | 206 | `ctx.addShape`、`text` |
| `slide10.<anonymous@215>(c, i)` | 215 | `Math.floor`、`box`、`text` |
| `slide10.<anonymous@224>(row, i)` | 224 | `text` |
| `slide10.<anonymous@228>(c, i)` | 228 | `Math.floor`、`box`、`text` |
| `slide10.<anonymous@236>(e, i)` | 236 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide10.<anonymous@245>(b, i)` | 245 | `Math.max`、`ctx.addShape`、`text` |
| `slide10.<anonymous@253>(c, i)` | 253 | `proofBand` |
| `slide10.<anonymous@257>(t, i)` | 257 | `Math.floor`、`box`、`text` |
| `slide10.<anonymous@268>(l, i)` | 268 | `arrow`、`box`、`text` |
| `slide10.<anonymous@277>(d, i)` | 277 | `text` |
| `slide10.<anonymous@281>(r, i)` | 281 | `box`、`text` |
| `slide10.<anonymous@290>(r, i)` | 290 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-11.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-11.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide11(presentation, ctx)` | 135 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide11.<anonymous@151>(m, i)` | 151 | `miniMetric` |
| `slide11.<anonymous@159>(p, i)` | 159 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide11.<anonymous@172>(l, i)` | 172 | `arrow`、`box`、`text` |
| `slide11.<anonymous@184>(s, i)` | 184 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide11.<anonymous@200>(g, i)` | 200 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide11.<anonymous@200>.<anonymous@205>(item, j)` | 205 | `ctx.addShape`、`text` |
| `slide11.<anonymous@214>(c, i)` | 214 | `Math.floor`、`box`、`text` |
| `slide11.<anonymous@223>(row, i)` | 223 | `text` |
| `slide11.<anonymous@227>(c, i)` | 227 | `Math.floor`、`box`、`text` |
| `slide11.<anonymous@235>(e, i)` | 235 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide11.<anonymous@244>(b, i)` | 244 | `Math.max`、`ctx.addShape`、`text` |
| `slide11.<anonymous@252>(c, i)` | 252 | `proofBand` |
| `slide11.<anonymous@256>(t, i)` | 256 | `Math.floor`、`box`、`text` |
| `slide11.<anonymous@267>(l, i)` | 267 | `arrow`、`box`、`text` |
| `slide11.<anonymous@276>(d, i)` | 276 | `text` |
| `slide11.<anonymous@280>(r, i)` | 280 | `box`、`text` |
| `slide11.<anonymous@289>(r, i)` | 289 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync-redesign/src/slides/slide-12.mjs`

`outputs/presentations/team-sync-redesign/src/slides/slide-12.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `text(slide, ctx, x, y, width, height, value, opts = {})` | 20 | `ctx.addText` |
| `box(slide, ctx, x, y, width, height, opts = {})` | 34 | `ctx.addShape`、`ctx.line` |
| `line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4)` | 42 | `ctx.addShape`、`ctx.line` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.steel)` | 53 | `ctx.addShape`、`ctx.line`、`line` |
| `circuit(slide, ctx, variant = "light")` | 66 | `line` |
| `frame(slide, ctx, data, n)` | 74 | `<dynamic>.padStart`、`String`、`circuit`、`ctx.addShape`、`text` |
| `sectionTag(slide, ctx, x, y, value, color = P.blue)` | 88 | `ctx.addShape`、`text` |
| `proofBand(slide, ctx, y, label, body, color = P.blue)` | 93 | `box`、`ctx.addShape`、`text` |
| `miniMetric(slide, ctx, x, y, value, label, color = P.blue)` | 100 | `box`、`ctx.addShape`、`text` |
| `slide12(presentation, ctx)` | 140 | `arrow`、`box`、`circuit`、`ctx.addShape`、`data.asks.join`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`frame`、`presentation.slides.add`、`proofBand`、`text` |
| `slide12.<anonymous@156>(m, i)` | 156 | `miniMetric` |
| `slide12.<anonymous@164>(p, i)` | 164 | `Math.floor`、`String`、`box`、`ctx.addShape`、`text` |
| `slide12.<anonymous@177>(l, i)` | 177 | `arrow`、`box`、`text` |
| `slide12.<anonymous@189>(s, i)` | 189 | `Math.floor`、`String`、`arrow`、`box`、`text` |
| `slide12.<anonymous@205>(g, i)` | 205 | `box`、`ctx.addShape`、`g[<computed>].forEach`、`text` |
| `slide12.<anonymous@205>.<anonymous@210>(item, j)` | 210 | `ctx.addShape`、`text` |
| `slide12.<anonymous@219>(c, i)` | 219 | `Math.floor`、`box`、`text` |
| `slide12.<anonymous@228>(row, i)` | 228 | `text` |
| `slide12.<anonymous@232>(c, i)` | 232 | `Math.floor`、`box`、`text` |
| `slide12.<anonymous@240>(e, i)` | 240 | `<dynamic>.join`、`box`、`e.slice`、`text` |
| `slide12.<anonymous@249>(b, i)` | 249 | `Math.max`、`ctx.addShape`、`text` |
| `slide12.<anonymous@257>(c, i)` | 257 | `proofBand` |
| `slide12.<anonymous@261>(t, i)` | 261 | `Math.floor`、`box`、`text` |
| `slide12.<anonymous@272>(l, i)` | 272 | `arrow`、`box`、`text` |
| `slide12.<anonymous@281>(d, i)` | 281 | `text` |
| `slide12.<anonymous@285>(r, i)` | 285 | `box`、`text` |
| `slide12.<anonymous@294>(r, i)` | 294 | `box`、`ctx.addShape`、`text` |

## `outputs/presentations/team-sync/src/create_slide_modules.mjs`

`outputs/presentations/team-sync/src/create_slide_modules.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `makeSlideSource(slide, index)` | 233 | `<dynamic>.padStart`、`JSON.stringify`、`String` |
| `main()` | 406 | `<dynamic>.padStart`、`String`、`fs.mkdir`、`fs.writeFile`、`makeSlideSource`、`path.join` |

模块级语法调用（含条件块，不等于一定发生）：`JSON.stringify`、`fileURLToPath`、`main`、`path.dirname`、`path.join`

## `outputs/presentations/team-sync/src/slides/slide-01.mjs`

`outputs/presentations/team-sync/src/slides/slide-01.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide01(presentation, ctx)` | 77 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide01.<anonymous@89>(m, i)` | 89 | `card`、`label` |
| `slide01.<anonymous@99>(p, i)` | 99 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide01.<anonymous@111>(l, i)` | 111 | `arrow`、`card`、`label` |
| `slide01.<anonymous@125>(s, i)` | 125 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide01.<anonymous@140>(g, i)` | 140 | `card`、`g[<computed>].forEach`、`label` |
| `slide01.<anonymous@140>.<anonymous@144>(item, j)` | 144 | `label` |
| `slide01.<anonymous@151>(c, i)` | 151 | `Math.floor`、`card`、`label` |
| `slide01.<anonymous@159>(line, i)` | 159 | `label` |
| `slide01.<anonymous@163>(c, i)` | 163 | `Math.floor`、`card`、`label` |
| `slide01.<anonymous@171>(e, i)` | 171 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide01.<anonymous@180>(b, i)` | 180 | `Math.max`、`ctx.addShape`、`label` |
| `slide01.<anonymous@188>(c, i)` | 188 | `bullet` |
| `slide01.<anonymous@192>(t, i)` | 192 | `Math.floor`、`card`、`label` |
| `slide01.<anonymous@204>(l, i)` | 204 | `arrow`、`card`、`label` |
| `slide01.<anonymous@213>(d, i)` | 213 | `label` |
| `slide01.<anonymous@217>(r, i)` | 217 | `card`、`label` |
| `slide01.<anonymous@226>(r, i)` | 226 | `card`、`label` |
| `slide01.<anonymous@235>(a, i)` | 235 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-02.mjs`

`outputs/presentations/team-sync/src/slides/slide-02.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide02(presentation, ctx)` | 74 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide02.<anonymous@86>(m, i)` | 86 | `card`、`label` |
| `slide02.<anonymous@96>(p, i)` | 96 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide02.<anonymous@108>(l, i)` | 108 | `arrow`、`card`、`label` |
| `slide02.<anonymous@122>(s, i)` | 122 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide02.<anonymous@137>(g, i)` | 137 | `card`、`g[<computed>].forEach`、`label` |
| `slide02.<anonymous@137>.<anonymous@141>(item, j)` | 141 | `label` |
| `slide02.<anonymous@148>(c, i)` | 148 | `Math.floor`、`card`、`label` |
| `slide02.<anonymous@156>(line, i)` | 156 | `label` |
| `slide02.<anonymous@160>(c, i)` | 160 | `Math.floor`、`card`、`label` |
| `slide02.<anonymous@168>(e, i)` | 168 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide02.<anonymous@177>(b, i)` | 177 | `Math.max`、`ctx.addShape`、`label` |
| `slide02.<anonymous@185>(c, i)` | 185 | `bullet` |
| `slide02.<anonymous@189>(t, i)` | 189 | `Math.floor`、`card`、`label` |
| `slide02.<anonymous@201>(l, i)` | 201 | `arrow`、`card`、`label` |
| `slide02.<anonymous@210>(d, i)` | 210 | `label` |
| `slide02.<anonymous@214>(r, i)` | 214 | `card`、`label` |
| `slide02.<anonymous@223>(r, i)` | 223 | `card`、`label` |
| `slide02.<anonymous@232>(a, i)` | 232 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-03.mjs`

`outputs/presentations/team-sync/src/slides/slide-03.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide03(presentation, ctx)` | 93 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide03.<anonymous@105>(m, i)` | 105 | `card`、`label` |
| `slide03.<anonymous@115>(p, i)` | 115 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide03.<anonymous@127>(l, i)` | 127 | `arrow`、`card`、`label` |
| `slide03.<anonymous@141>(s, i)` | 141 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide03.<anonymous@156>(g, i)` | 156 | `card`、`g[<computed>].forEach`、`label` |
| `slide03.<anonymous@156>.<anonymous@160>(item, j)` | 160 | `label` |
| `slide03.<anonymous@167>(c, i)` | 167 | `Math.floor`、`card`、`label` |
| `slide03.<anonymous@175>(line, i)` | 175 | `label` |
| `slide03.<anonymous@179>(c, i)` | 179 | `Math.floor`、`card`、`label` |
| `slide03.<anonymous@187>(e, i)` | 187 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide03.<anonymous@196>(b, i)` | 196 | `Math.max`、`ctx.addShape`、`label` |
| `slide03.<anonymous@204>(c, i)` | 204 | `bullet` |
| `slide03.<anonymous@208>(t, i)` | 208 | `Math.floor`、`card`、`label` |
| `slide03.<anonymous@220>(l, i)` | 220 | `arrow`、`card`、`label` |
| `slide03.<anonymous@229>(d, i)` | 229 | `label` |
| `slide03.<anonymous@233>(r, i)` | 233 | `card`、`label` |
| `slide03.<anonymous@242>(r, i)` | 242 | `card`、`label` |
| `slide03.<anonymous@251>(a, i)` | 251 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-04.mjs`

`outputs/presentations/team-sync/src/slides/slide-04.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide04(presentation, ctx)` | 90 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide04.<anonymous@102>(m, i)` | 102 | `card`、`label` |
| `slide04.<anonymous@112>(p, i)` | 112 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide04.<anonymous@124>(l, i)` | 124 | `arrow`、`card`、`label` |
| `slide04.<anonymous@138>(s, i)` | 138 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide04.<anonymous@153>(g, i)` | 153 | `card`、`g[<computed>].forEach`、`label` |
| `slide04.<anonymous@153>.<anonymous@157>(item, j)` | 157 | `label` |
| `slide04.<anonymous@164>(c, i)` | 164 | `Math.floor`、`card`、`label` |
| `slide04.<anonymous@172>(line, i)` | 172 | `label` |
| `slide04.<anonymous@176>(c, i)` | 176 | `Math.floor`、`card`、`label` |
| `slide04.<anonymous@184>(e, i)` | 184 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide04.<anonymous@193>(b, i)` | 193 | `Math.max`、`ctx.addShape`、`label` |
| `slide04.<anonymous@201>(c, i)` | 201 | `bullet` |
| `slide04.<anonymous@205>(t, i)` | 205 | `Math.floor`、`card`、`label` |
| `slide04.<anonymous@217>(l, i)` | 217 | `arrow`、`card`、`label` |
| `slide04.<anonymous@226>(d, i)` | 226 | `label` |
| `slide04.<anonymous@230>(r, i)` | 230 | `card`、`label` |
| `slide04.<anonymous@239>(r, i)` | 239 | `card`、`label` |
| `slide04.<anonymous@248>(a, i)` | 248 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-05.mjs`

`outputs/presentations/team-sync/src/slides/slide-05.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide05(presentation, ctx)` | 83 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide05.<anonymous@95>(m, i)` | 95 | `card`、`label` |
| `slide05.<anonymous@105>(p, i)` | 105 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide05.<anonymous@117>(l, i)` | 117 | `arrow`、`card`、`label` |
| `slide05.<anonymous@131>(s, i)` | 131 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide05.<anonymous@146>(g, i)` | 146 | `card`、`g[<computed>].forEach`、`label` |
| `slide05.<anonymous@146>.<anonymous@150>(item, j)` | 150 | `label` |
| `slide05.<anonymous@157>(c, i)` | 157 | `Math.floor`、`card`、`label` |
| `slide05.<anonymous@165>(line, i)` | 165 | `label` |
| `slide05.<anonymous@169>(c, i)` | 169 | `Math.floor`、`card`、`label` |
| `slide05.<anonymous@177>(e, i)` | 177 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide05.<anonymous@186>(b, i)` | 186 | `Math.max`、`ctx.addShape`、`label` |
| `slide05.<anonymous@194>(c, i)` | 194 | `bullet` |
| `slide05.<anonymous@198>(t, i)` | 198 | `Math.floor`、`card`、`label` |
| `slide05.<anonymous@210>(l, i)` | 210 | `arrow`、`card`、`label` |
| `slide05.<anonymous@219>(d, i)` | 219 | `label` |
| `slide05.<anonymous@223>(r, i)` | 223 | `card`、`label` |
| `slide05.<anonymous@232>(r, i)` | 232 | `card`、`label` |
| `slide05.<anonymous@241>(a, i)` | 241 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-06.mjs`

`outputs/presentations/team-sync/src/slides/slide-06.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide06(presentation, ctx)` | 83 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide06.<anonymous@95>(m, i)` | 95 | `card`、`label` |
| `slide06.<anonymous@105>(p, i)` | 105 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide06.<anonymous@117>(l, i)` | 117 | `arrow`、`card`、`label` |
| `slide06.<anonymous@131>(s, i)` | 131 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide06.<anonymous@146>(g, i)` | 146 | `card`、`g[<computed>].forEach`、`label` |
| `slide06.<anonymous@146>.<anonymous@150>(item, j)` | 150 | `label` |
| `slide06.<anonymous@157>(c, i)` | 157 | `Math.floor`、`card`、`label` |
| `slide06.<anonymous@165>(line, i)` | 165 | `label` |
| `slide06.<anonymous@169>(c, i)` | 169 | `Math.floor`、`card`、`label` |
| `slide06.<anonymous@177>(e, i)` | 177 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide06.<anonymous@186>(b, i)` | 186 | `Math.max`、`ctx.addShape`、`label` |
| `slide06.<anonymous@194>(c, i)` | 194 | `bullet` |
| `slide06.<anonymous@198>(t, i)` | 198 | `Math.floor`、`card`、`label` |
| `slide06.<anonymous@210>(l, i)` | 210 | `arrow`、`card`、`label` |
| `slide06.<anonymous@219>(d, i)` | 219 | `label` |
| `slide06.<anonymous@223>(r, i)` | 223 | `card`、`label` |
| `slide06.<anonymous@232>(r, i)` | 232 | `card`、`label` |
| `slide06.<anonymous@241>(a, i)` | 241 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-07.mjs`

`outputs/presentations/team-sync/src/slides/slide-07.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide07(presentation, ctx)` | 92 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide07.<anonymous@104>(m, i)` | 104 | `card`、`label` |
| `slide07.<anonymous@114>(p, i)` | 114 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide07.<anonymous@126>(l, i)` | 126 | `arrow`、`card`、`label` |
| `slide07.<anonymous@140>(s, i)` | 140 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide07.<anonymous@155>(g, i)` | 155 | `card`、`g[<computed>].forEach`、`label` |
| `slide07.<anonymous@155>.<anonymous@159>(item, j)` | 159 | `label` |
| `slide07.<anonymous@166>(c, i)` | 166 | `Math.floor`、`card`、`label` |
| `slide07.<anonymous@174>(line, i)` | 174 | `label` |
| `slide07.<anonymous@178>(c, i)` | 178 | `Math.floor`、`card`、`label` |
| `slide07.<anonymous@186>(e, i)` | 186 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide07.<anonymous@195>(b, i)` | 195 | `Math.max`、`ctx.addShape`、`label` |
| `slide07.<anonymous@203>(c, i)` | 203 | `bullet` |
| `slide07.<anonymous@207>(t, i)` | 207 | `Math.floor`、`card`、`label` |
| `slide07.<anonymous@219>(l, i)` | 219 | `arrow`、`card`、`label` |
| `slide07.<anonymous@228>(d, i)` | 228 | `label` |
| `slide07.<anonymous@232>(r, i)` | 232 | `card`、`label` |
| `slide07.<anonymous@241>(r, i)` | 241 | `card`、`label` |
| `slide07.<anonymous@250>(a, i)` | 250 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-08.mjs`

`outputs/presentations/team-sync/src/slides/slide-08.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide08(presentation, ctx)` | 83 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide08.<anonymous@95>(m, i)` | 95 | `card`、`label` |
| `slide08.<anonymous@105>(p, i)` | 105 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide08.<anonymous@117>(l, i)` | 117 | `arrow`、`card`、`label` |
| `slide08.<anonymous@131>(s, i)` | 131 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide08.<anonymous@146>(g, i)` | 146 | `card`、`g[<computed>].forEach`、`label` |
| `slide08.<anonymous@146>.<anonymous@150>(item, j)` | 150 | `label` |
| `slide08.<anonymous@157>(c, i)` | 157 | `Math.floor`、`card`、`label` |
| `slide08.<anonymous@165>(line, i)` | 165 | `label` |
| `slide08.<anonymous@169>(c, i)` | 169 | `Math.floor`、`card`、`label` |
| `slide08.<anonymous@177>(e, i)` | 177 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide08.<anonymous@186>(b, i)` | 186 | `Math.max`、`ctx.addShape`、`label` |
| `slide08.<anonymous@194>(c, i)` | 194 | `bullet` |
| `slide08.<anonymous@198>(t, i)` | 198 | `Math.floor`、`card`、`label` |
| `slide08.<anonymous@210>(l, i)` | 210 | `arrow`、`card`、`label` |
| `slide08.<anonymous@219>(d, i)` | 219 | `label` |
| `slide08.<anonymous@223>(r, i)` | 223 | `card`、`label` |
| `slide08.<anonymous@232>(r, i)` | 232 | `card`、`label` |
| `slide08.<anonymous@241>(a, i)` | 241 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-09.mjs`

`outputs/presentations/team-sync/src/slides/slide-09.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide09(presentation, ctx)` | 75 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide09.<anonymous@87>(m, i)` | 87 | `card`、`label` |
| `slide09.<anonymous@97>(p, i)` | 97 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide09.<anonymous@109>(l, i)` | 109 | `arrow`、`card`、`label` |
| `slide09.<anonymous@123>(s, i)` | 123 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide09.<anonymous@138>(g, i)` | 138 | `card`、`g[<computed>].forEach`、`label` |
| `slide09.<anonymous@138>.<anonymous@142>(item, j)` | 142 | `label` |
| `slide09.<anonymous@149>(c, i)` | 149 | `Math.floor`、`card`、`label` |
| `slide09.<anonymous@157>(line, i)` | 157 | `label` |
| `slide09.<anonymous@161>(c, i)` | 161 | `Math.floor`、`card`、`label` |
| `slide09.<anonymous@169>(e, i)` | 169 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide09.<anonymous@178>(b, i)` | 178 | `Math.max`、`ctx.addShape`、`label` |
| `slide09.<anonymous@186>(c, i)` | 186 | `bullet` |
| `slide09.<anonymous@190>(t, i)` | 190 | `Math.floor`、`card`、`label` |
| `slide09.<anonymous@202>(l, i)` | 202 | `arrow`、`card`、`label` |
| `slide09.<anonymous@211>(d, i)` | 211 | `label` |
| `slide09.<anonymous@215>(r, i)` | 215 | `card`、`label` |
| `slide09.<anonymous@224>(r, i)` | 224 | `card`、`label` |
| `slide09.<anonymous@233>(a, i)` | 233 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-10.mjs`

`outputs/presentations/team-sync/src/slides/slide-10.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide10(presentation, ctx)` | 79 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide10.<anonymous@91>(m, i)` | 91 | `card`、`label` |
| `slide10.<anonymous@101>(p, i)` | 101 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide10.<anonymous@113>(l, i)` | 113 | `arrow`、`card`、`label` |
| `slide10.<anonymous@127>(s, i)` | 127 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide10.<anonymous@142>(g, i)` | 142 | `card`、`g[<computed>].forEach`、`label` |
| `slide10.<anonymous@142>.<anonymous@146>(item, j)` | 146 | `label` |
| `slide10.<anonymous@153>(c, i)` | 153 | `Math.floor`、`card`、`label` |
| `slide10.<anonymous@161>(line, i)` | 161 | `label` |
| `slide10.<anonymous@165>(c, i)` | 165 | `Math.floor`、`card`、`label` |
| `slide10.<anonymous@173>(e, i)` | 173 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide10.<anonymous@182>(b, i)` | 182 | `Math.max`、`ctx.addShape`、`label` |
| `slide10.<anonymous@190>(c, i)` | 190 | `bullet` |
| `slide10.<anonymous@194>(t, i)` | 194 | `Math.floor`、`card`、`label` |
| `slide10.<anonymous@206>(l, i)` | 206 | `arrow`、`card`、`label` |
| `slide10.<anonymous@215>(d, i)` | 215 | `label` |
| `slide10.<anonymous@219>(r, i)` | 219 | `card`、`label` |
| `slide10.<anonymous@228>(r, i)` | 228 | `card`、`label` |
| `slide10.<anonymous@237>(a, i)` | 237 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-11.mjs`

`outputs/presentations/team-sync/src/slides/slide-11.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide11(presentation, ctx)` | 78 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide11.<anonymous@90>(m, i)` | 90 | `card`、`label` |
| `slide11.<anonymous@100>(p, i)` | 100 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide11.<anonymous@112>(l, i)` | 112 | `arrow`、`card`、`label` |
| `slide11.<anonymous@126>(s, i)` | 126 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide11.<anonymous@141>(g, i)` | 141 | `card`、`g[<computed>].forEach`、`label` |
| `slide11.<anonymous@141>.<anonymous@145>(item, j)` | 145 | `label` |
| `slide11.<anonymous@152>(c, i)` | 152 | `Math.floor`、`card`、`label` |
| `slide11.<anonymous@160>(line, i)` | 160 | `label` |
| `slide11.<anonymous@164>(c, i)` | 164 | `Math.floor`、`card`、`label` |
| `slide11.<anonymous@172>(e, i)` | 172 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide11.<anonymous@181>(b, i)` | 181 | `Math.max`、`ctx.addShape`、`label` |
| `slide11.<anonymous@189>(c, i)` | 189 | `bullet` |
| `slide11.<anonymous@193>(t, i)` | 193 | `Math.floor`、`card`、`label` |
| `slide11.<anonymous@205>(l, i)` | 205 | `arrow`、`card`、`label` |
| `slide11.<anonymous@214>(d, i)` | 214 | `label` |
| `slide11.<anonymous@218>(r, i)` | 218 | `card`、`label` |
| `slide11.<anonymous@227>(r, i)` | 227 | `card`、`label` |
| `slide11.<anonymous@236>(a, i)` | 236 | `label` |

## `outputs/presentations/team-sync/src/slides/slide-12.mjs`

`outputs/presentations/team-sync/src/slides/slide-12.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `addBg(slide, ctx, title, claim)` | 17 | `ctx.addShape`、`ctx.addText` |
| `addFooter(slide, ctx, n)` | 25 | `<dynamic>.padStart`、`String`、`ctx.addShape`、`ctx.addText` |
| `card(slide, ctx, x, y, w, h, opts = {})` | 31 | `ctx.addShape`、`ctx.line` |
| `label(slide, ctx, x, y, w, h, text, opts = {})` | 35 | `ctx.addText` |
| `bullet(slide, ctx, x, y, title, body, color = P.blue)` | 39 | `ctx.addShape`、`label` |
| `arrow(slide, ctx, x1, y1, x2, y2, color = P.blue)` | 45 | `ctx.addShape`、`ctx.line` |
| `slide12(presentation, ctx)` | 83 | `addBg`、`addFooter`、`arrow`、`card`、`ctx.addShape`、`data.asks.forEach`、`data.bars.forEach`、`data.callouts.forEach`、`data.cards.forEach`、`data.checks.forEach`、`data.done.forEach`、`data.examples.forEach`、`data.groups.forEach`、`data.lanes.forEach`、`data.layers.forEach`、`data.metrics.forEach`、`data.points.forEach`、`data.roadmap.forEach`、`data.roles.forEach`、`data.snippet.forEach`、`data.steps.forEach`、`data.templates.forEach`、`label`、`presentation.slides.add` |
| `slide12.<anonymous@95>(m, i)` | 95 | `card`、`label` |
| `slide12.<anonymous@105>(p, i)` | 105 | `Math.floor`、`card`、`ctx.addShape`、`label` |
| `slide12.<anonymous@117>(l, i)` | 117 | `arrow`、`card`、`label` |
| `slide12.<anonymous@131>(s, i)` | 131 | `Math.floor`、`String`、`arrow`、`card`、`label` |
| `slide12.<anonymous@146>(g, i)` | 146 | `card`、`g[<computed>].forEach`、`label` |
| `slide12.<anonymous@146>.<anonymous@150>(item, j)` | 150 | `label` |
| `slide12.<anonymous@157>(c, i)` | 157 | `Math.floor`、`card`、`label` |
| `slide12.<anonymous@165>(line, i)` | 165 | `label` |
| `slide12.<anonymous@169>(c, i)` | 169 | `Math.floor`、`card`、`label` |
| `slide12.<anonymous@177>(e, i)` | 177 | `<dynamic>.join`、`card`、`e.slice`、`label` |
| `slide12.<anonymous@186>(b, i)` | 186 | `Math.max`、`ctx.addShape`、`label` |
| `slide12.<anonymous@194>(c, i)` | 194 | `bullet` |
| `slide12.<anonymous@198>(t, i)` | 198 | `Math.floor`、`card`、`label` |
| `slide12.<anonymous@210>(l, i)` | 210 | `arrow`、`card`、`label` |
| `slide12.<anonymous@219>(d, i)` | 219 | `label` |
| `slide12.<anonymous@223>(r, i)` | 223 | `card`、`label` |
| `slide12.<anonymous@232>(r, i)` | 232 | `card`、`label` |
| `slide12.<anonymous@241>(a, i)` | 241 | `label` |

## `outputs/presentations/team-task-brief/src/build_hnai_fpga_team_brief.mjs`

`outputs/presentations/team-task-brief/src/build_hnai_fpga_team_brief.mjs`

| 定义 / 参数 | 行 | 函数体中的直接调用表达式 |
| --- | ---: | --- |
| `<anonymous@12>(err)` | 12 | `<dynamic>.join`、`<dynamic>.slice`、`<dynamic>.split`、`String`、`console.error`、`process.exit` |
| `tx(value, x, y, w, h, style = {})` | 45 | `text` |
| `box(x, y, w, h, fill = C.panel, line = C.line, radius = 8)` | 59 | `shape` |
| `pill(label, x, y, w, color, fill)` | 70 | `layers`、`shape`、`text` |
| `header(slide, title, kicker = "HNAI-FPGA team brief")` | 82 | `layers`、`shape`、`slide.compose`、`tx` |
| `addSlide(title, kicker)` | 92 | `header`、`p.slides.add` |
| `bulletList(items, x, y, w, gap = 48, color = C.blue)` | 98 | `items.forEach` |
| `bulletList.<anonymous@100>(item, i)` | 100 | `children.push`、`shape`、`tx` |
| `metric(label, value, note, x, y, w, color, fill)` | 108 | `layers`、`shape`、`text` |
| `flowNode(label, sub, x, y, w, color, fill)` | 117 | `layers`、`shape`、`text` |
| `line(x1, y1, x2, y2, color = C.blue)` | 125 | `Math.abs`、`Math.max`、`Math.min`、`shape` |
| `<anonymous@224>(r, i)` | 224 | `box`、`children.push`、`shape`、`tx` |
| `<anonymous@247>(c, i)` | 247 | `box`、`bulletList`、`children.push`、`tx` |
| `<anonymous@302>(it, i)` | 302 | `Math.floor`、`box`、`children.push`、`tx` |
| `<anonymous@327>(h, i)` | 327 | `children.push`、`tx` |
| `<anonymous@328>(r, ri)` | 328 | `children.push`、`r.forEach`、`shape` |
| `<anonymous@328>.<anonymous@331>(v, i)` | 331 | `children.push`、`tx` |
| `<anonymous@349>(w, i)` | 349 | `Math.floor`、`box`、`children.push`、`tx` |
| `<anonymous@371>(ph, i)` | 371 | `box`、`children.push`、`line`、`shape`、`tx` |

模块级语法调用（含条件块，不等于一定发生）：`Buffer.from`、`Presentation.create`、`PresentationFile.exportPptx`、`addSlide`、`box`、`bulletList`、`children.push`、`cols.forEach`、`console.log`、`fileURLToPath`、`flowNode`、`headers.forEach`、`items.forEach`、`layers`、`layersData.forEach`、`line`、`metric`、`mkdir`、`new URL`、`p.slides.add`、`path.join`、`phases.forEach`、`process.on`、`rows.forEach`、`s.compose`、`shape`、`tx`、`wp.forEach`、`writeFile`

合计：68 个文件，795 个函数/箭头回调定义，3909 个语法调用位置。
