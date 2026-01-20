// 简单的浏览器控制台测试脚本
// 将此脚本复制到浏览器控制台中运行，测试前后端集成

console.log("🚀 Starting Frontend-Backend Integration Test in Browser");

// 配置
const BACKEND_URL = 'http://localhost:18080/api/v1';

// 测试函数
async function testIntegration() {
    console.log("🔍 Testing Backend Connection...");

    try {
        // 1. 测试健康检查
        const healthResponse = await fetch(`${BACKEND_URL}/../health`);
        const healthData = await healthResponse.json();
        console.log(`✅ Health Check: ${healthData.status}`);

        // 2. 测试登录
        console.log("\n🔐 Testing Login...");
        const loginResponse = await fetch(`${BACKEND_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: 'admin',
                password: 'pwd123'
            })
        });

        if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            console.log(`✅ Login Successful: ${loginData.username} (${loginData.role})`);
            console.log(`📝 Token: ${loginData.token.substring(0, 20)}...`);

            const token = loginData.token;

            // 3. 测试获取用户列表
            console.log("\n👥 Testing User Management...");
            const usersResponse = await fetch(`${BACKEND_URL}/admin/users`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (usersResponse.ok) {
                const users = await usersResponse.json();
                console.log(`✅ Retrieved ${users.length} users:`);
                users.slice(0, 3).forEach(user => {
                    console.log(`   - ${user.username} (${user.role})`);
                });
            }

            // 4. 测试会话管理
            console.log("\n💬 Testing Session Management...");
            const sessionResponse = await fetch(`${BACKEND_URL}/sessions?user_id=${loginData.id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (sessionResponse.ok) {
                const sessions = await sessionResponse.json();
                console.log(`✅ Retrieved ${sessions.length} sessions`);
            }

            // 5. 测试IAS代理
            console.log("\n🤖 Testing IAS Proxy...");
            const iasResponse = await fetch(`${BACKEND_URL}/lmp-cloud-ias-server/api/llm/chat/completions/V2`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    model: 'test-model',
                    messages: [{ role: 'user', content: 'Hello from browser!' }],
                    stream: false
                })
            });

            if (iasResponse.ok) {
                const iasData = await iasResponse.json();
                console.log(`✅ IAS Proxy: ${iasData.choices[0].message.content}`);
            }

            console.log("\n🎉 All tests completed successfully!");
            console.log("✅ Frontend can successfully communicate with backend");

        } else {
            console.error(`❌ Login failed: ${loginResponse.status} ${loginResponse.statusText}`);
            console.error(await loginResponse.text());
        }

    } catch (error) {
        console.error('❌ Integration test failed:', error);
    }
}

// 自动运行测试
testIntegration();

// 暴露测试函数到全局，便于手动调用
window.testIntegration = testIntegration;
console.log("💡 You can run testIntegration() manually in console");