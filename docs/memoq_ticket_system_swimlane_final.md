# MemoQ 工单系统流程图

```mermaid
sequenceDiagram
    participant C as 客户用户
    participant S as 技术支持
    participant SA as 技术支持管理员
    participant A as 系统管理员
    participant SYS as 系统

    %% 用户注册与登录流程
    rect rgb(240, 248, 255)
        Note over C, SYS: 用户注册与登录流程
        C->>SYS: 访问公司专属登录URL
        SYS->>C: 显示登录页面(MemoQ Logo + 公司Logo)
        C->>SYS: 选择登录方式(账号密码/SSO)
        alt 账号密码登录
            C->>SYS: 输入用户名和密码
            SYS->>SYS: 验证凭据
        else SSO登录
            C->>SYS: 点击SSO登录按钮
            SYS->>SYS: 重定向到SSO提供商
            SYS->>C: 完成SSO认证
        end
        SYS->>SYS: 验证用户角色
        alt 客户用户
            SYS->>C: 重定向到客户Dashboard
        else 技术支持
            SYS->>S: 重定向到技术支持Dashboard
        else 技术支持管理员
            SYS->>SA: 重定向到技术支持管理员Dashboard
        else 系统管理员
            SYS->>A: 重定向到系统管理员Dashboard
        end
    end
   %% 工单创建流程
    rect rgb(255, 240, 245)
        Note over C, SYS: 工单创建流程
        alt 客户创建工单
            C->>SYS: 点击"创建工单"按钮
            SYS->>C: 显示工单创建表单
            C->>SYS: 填写工单信息(标题、描述、类型等)
            C->>SYS: 上传附件(可选)
            C->>SYS: 添加关注人(可选)
            C->>SYS: 提交工单
        else 技术支持代客户创建工单
            S->>SYS: 点击"代客户创建工单"按钮
            SYS->>S: 显示工单创建表单
            S->>SYS: 选择客户公司
            S->>SYS: 填写工单信息(标题、描述、类型等)
            S->>SYS: 指定提交人
            S->>SYS: 上传附件(可选)
            S->>SYS: 添加关注人(可选)
            S->>SYS: 提交工单
        end
        SYS->>SYS: 创建工单记录
        SYS->>SYS: 生成工单URL(/companyname/xxxx)
        SYS->>SYS: 设置工单状态为"新建工单"
        alt 邮件通知已启用
            SYS->>SYS: 发送工单创建邮件通知
        end
        alt Webhook已配置
            SYS->>SYS: 触发工单创建Webhook
        end
    end

    %% 工单分配流程
    rect rgb(240, 255, 240)
        Note over SA, SYS: 工单分配流程
        SYS->>SA: 在Dashboard显示待分配工单
        SA->>SYS: 查看待分配工单详情
        SA->>SYS: 选择技术支持人员
        SA->>SYS: 确认分配
        SYS->>SYS: 更新工单状态为"处理中"
        SYS->>SYS: 记录工单分配历史
        SYS->>S: 通知技术支持人员
        alt 邮件通知已启用
            SYS->>SYS: 发送工单分配邮件通知
        end
        alt Webhook已配置
            SYS->>SYS: 触发工单分配Webhook
        end
    end

    %% 工单处理流程
    rect rgb(255, 248, 220)
        Note over S, C: 工单处理流程
        S->>SYS: 查看已分配工单
        S->>SYS: 打开工单详情
        S->>SYS: 分析工单问题
        alt 需要更多信息
            S->>SYS: 回复客户请求更多信息
            SYS->>SYS: 更新工单状态为"等待客户回复"
            SYS->>C: 通知客户有新回复
            alt 邮件通知已启用
                SYS->>SYS: 发送新回复邮件通知
            end
            C->>SYS: 查看工单详情
            C->>SYS: 提供额外信息
            SYS->>SYS: 更新工单状态为"客户已回复"
            SYS->>S: 通知技术支持客户已回复
        else 可以直接解决
            S->>SYS: 回复解决方案
            S->>SYS: 上传附件(可选)
            S->>SYS: 更新工单状态为"已解决"
            SYS->>C: 通知客户工单已解决
            alt 邮件通知已启用
                SYS->>SYS: 发送工单解决邮件通知
            end
        else 需要转移工单
            S->>SYS: 点击"转移工单"按钮
            SYS->>S: 显示转移工单表单
            S->>SYS: 选择目标技术支持
            S->>SYS: 填写转移原因
            S->>SYS: 确认转移
            SYS->>SYS: 记录工单转移历史
            SYS->>SYS: 通知新技术支持
        else 需要暂停工单
            S->>SYS: 点击"暂停工单"按钮
            SYS->>S: 显示暂停工单表单
            S->>SYS: 填写暂停原因
            S->>SYS: 确认暂停
            SYS->>SYS: 更新工单状态为"已暂停"
            SYS->>SYS: 暂停SLA和idle计时
            SYS->>C: 通知客户工单已暂停
            alt 邮件通知已启用
                SYS->>SYS: 发送工单暂停邮件通知
            end
        end
    end

    %% 工单关闭流程
    rect rgb(230, 230, 250)
        Note over C, S: 工单关闭流程
        alt 客户确认关闭
            C->>SYS: 确认问题已解决
            C->>SYS: 点击"关闭工单"按钮
            SYS->>C: 显示满意度评价表单
            C->>SYS: 提交满意度评价
        else 技术支持关闭
            S->>SYS: 点击"关闭工单"按钮
            SYS->>S: 显示关闭原因表单
            S->>SYS: 填写关闭原因
            S->>SYS: 确认关闭
        end
        SYS->>SYS: 更新工单状态为"已关闭"
        SYS->>SYS: 记录工单关闭历史
        alt 邮件通知已启用
            SYS->>SYS: 发送工单关闭邮件通知
        end
        alt Webhook已配置
            SYS->>SYS: 触发工单关闭Webhook
        end
    end

    %% 工单类型管理流程
    rect rgb(245, 245, 220)
        Note over A, SA, S: 工单类型管理流程
        alt 系统管理员创建工单类型
            A->>SYS: 访问工单类型管理页面
            A->>SYS: 点击"创建工单类型"按钮
            SYS->>A: 显示工单类型表单
            A->>SYS: 填写类型信息(名称、描述等)
            A->>SYS: 选择父类型(可选)
            A->>SYS: 提交表单
        else 技术支持管理员创建工单类型
            SA->>SYS: 访问工单类型管理页面
            SA->>SYS: 点击"创建工单类型"按钮
            SYS->>SA: 显示工单类型表单
            SA->>SYS: 填写类型信息(名称、描述等)
            SA->>SYS: 选择父类型(可选)
            SA->>SYS: 提交表单
        else 技术支持创建工单类型
            S->>SYS: 访问工单类型管理页面
            S->>SYS: 点击"创建工单类型"按钮
            SYS->>S: 显示工单类型表单
            S->>SYS: 填写类型信息(名称、描述等)
            S->>SYS: 选择父类型(可选)
            S->>SYS: 提交表单
        end
        SYS->>SYS: 创建工单类型记录
        SYS->>SYS: 更新工单类型树
    end

    %% 工单标签管理流程
    rect rgb(230, 255, 230)
        Note over A, SA, S: 工单标签管理流程
        alt 系统管理员管理标签
            A->>SYS: 访问工单标签管理页面
            A->>SYS: 创建/编辑/删除标签
        else 技术支持管理员管理标签
            SA->>SYS: 访问工单标签管理页面
            SA->>SYS: 创建/编辑/删除标签
        else 技术支持管理标签
            S->>SYS: 访问工单标签管理页面
            S->>SYS: 创建/编辑/删除标签
        end
        SYS->>SYS: 更新工单标签数据
    end

    %% 公司管理流程
    rect rgb(255, 228, 225)
        Note over A, SA: 公司管理流程
        alt 系统管理员管理公司
            A->>SYS: 访问公司管理页面
            A->>SYS: 创建/编辑/删除公司
        else 技术支持管理员管理公司
            SA->>SYS: 访问公司管理页面
            SA->>SYS: 创建/编辑/删除公司
        end
        SYS->>SYS: 更新公司信息
        SYS->>SYS: 生成公司专属URL
    end

    %% 邮件系统配置流程
    rect rgb(220, 220, 255)
        Note over A, SA: 邮件系统配置流程
        alt 系统管理员配置邮件系统
            A->>SYS: 访问邮件系统配置页面
            A->>SYS: 配置SMTP服务器信息
            A->>SYS: 创建/编辑邮件模板
            A->>SYS: 测试邮件发送
        else 技术支持管理员配置邮件系统
            SA->>SYS: 访问邮件系统配置页面
            SA->>SYS: 配置SMTP服务器信息
            SA->>SYS: 创建/编辑邮件模板
            SA->>SYS: 测试邮件发送
        end
        SYS->>SYS: 保存邮件配置
    end

    %% Webhook配置流程
    rect rgb(255, 222, 173)
        Note over A, SA: Webhook配置流程
        alt 系统管理员配置Webhook
            A->>SYS: 访问Webhook配置页面
            A->>SYS: 添加Webhook URL
            A->>SYS: 选择事件类型
            A->>SYS: 配置请求头和认证信息
            A->>SYS: 测试Webhook
        else 技术支持管理员配置Webhook
            SA->>SYS: 访问Webhook配置页面
            SA->>SYS: 添加Webhook URL
            SA->>SYS: 选择事件类型
            SA->>SYS: 配置请求头和认证信息
            SA->>SYS: 测试Webhook
        end
        SYS->>SYS: 保存Webhook配置
    end

    %% SLA监控流程
    rect rgb(255, 235, 205)
        Note over SA, SYS: SLA监控流程
        SYS->>SYS: 计算工单SLA状态
        SYS->>SYS: 更新即将Miss IR和已Miss IR工单列表
        SYS->>SA: 在Dashboard显示SLA监控表格
        SA->>SYS: 查看SLA监控表格
        SA->>SYS: 采取措施(分配/调整优先级等)
    end

    %% 工单闲置监控流程
    rect rgb(240, 255, 255)
        Note over SA, SYS: 工单闲置监控流程
        SYS->>SYS: 计算工单闲置状态
        SYS->>SYS: 更新即将Idle和已Idle工单列表
        SYS->>SA: 在Dashboard显示闲置监控表格
        SA->>SYS: 查看闲置监控表格
        SA->>SYS: 采取措施(提醒技术支持等)
    end

    %% 公司用户工单查看流程
    rect rgb(250, 240, 230)
        Note over C, SYS: 公司用户工单查看流程
        C->>SYS: 访问客户Dashboard
        SYS->>C: 显示"我的活跃工单"
        SYS->>C: 显示"需要我关注的工单"
        SYS->>C: 显示"公司所有工单"
        C->>SYS: 点击工单标题
        SYS->>C: 显示工单详情页面
        C->>SYS: 查看工单回复历史
        C->>SYS: 查看工单附件
        C->>SYS: 查看工单时间线
    end
```
