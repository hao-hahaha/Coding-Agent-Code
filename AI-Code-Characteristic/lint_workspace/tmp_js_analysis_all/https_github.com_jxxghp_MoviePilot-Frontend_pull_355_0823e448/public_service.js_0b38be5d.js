const path = require('node:path')
const express = require('express')
const proxy = require('express-http-proxy')
const { createProxyMiddleware } = require('http-proxy-middleware')

const app = express()
const port = process.env.NGINX_PORT || 3000

// 后端 API 地址
const proxyConfig = {
  URL: '127.0.0.1',
  PORT: process.env.PORT || 3001
}

// 静态文件服务目录
app.use(express.static(__dirname))

// 创建专门的SSE代理中间件
const sseProxyMiddleware = createProxyMiddleware({
  target: `http://${proxyConfig.URL}:${proxyConfig.PORT}`,
  changeOrigin: true,
  ws: false,
  timeout: 0, // 无超时
  proxyTimeout: 0, // 无超时
  headers: {
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache'
  },
  onProxyRes: (proxyRes, req, res) => {
    // 检测SSE响应
    const isSSE = proxyRes.headers['content-type'] && 
                  proxyRes.headers['content-type'].includes('text/event-stream');
    
    if (isSSE) {
      // 设置SSE响应头
      res.writeHead(proxyRes.statusCode, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control, Content-Type, Authorization'
      });
      
      // 直接将代理响应流式传输到客户端
      proxyRes.pipe(res);
      
      // 处理客户端断开连接
      req.on('close', () => {
        console.log('Client disconnected from SSE stream');
        if (proxyRes.destroy) {
          proxyRes.destroy();
        }
      });
      
      // 处理代理响应结束
      proxyRes.on('end', () => {
        console.log('SSE stream ended');
        if (!res.headersSent) {
          res.end();
        }
      });
      
      // 处理代理响应错误
      proxyRes.on('error', (err) => {
        console.error('SSE proxy response error:', err);
        if (!res.headersSent) {
          res.status(500).end();
        }
      });
    }
  },
  onError: (err, req, res) => {
    console.error('SSE proxy error:', err);
    if (!res.headersSent) {
      res.status(500).json({ error: 'Proxy error' });
    }
  }
});

// 创建普通API代理中间件
const apiProxyMiddleware = proxy(`${proxyConfig.URL}:${proxyConfig.PORT}`, {
  // 路径加上 /api 前缀
  proxyReqPathResolver: (req) => {
    return `/api${req.url}`
  },
  proxyReqOptDecorator: (proxyReqOpts, srcReq) => {
    proxyReqOpts.headers = proxyReqOpts.headers || {};
    
    // 检测是否为SSE请求
    const isSSE = srcReq.headers.accept && srcReq.headers.accept.includes('text/event-stream');
    
    if (!isSSE) {
      // 普通请求设置超时
      proxyReqOpts.timeout = 600000; // 600秒超时
    }
    
    return proxyReqOpts;
  },
  userResDecorator: (proxyRes, proxyResData, userReq, userRes) => {
    // 只处理非SSE响应
    const isSSEResponse = proxyRes.headers['content-type'] && 
                         proxyRes.headers['content-type'].includes('text/event-stream');
    
    if (!isSSEResponse) {
      // 普通响应：正常处理
      return proxyResData;
    }
    
    // SSE响应不在这里处理，已经由专门的中间件处理
    return proxyResData;
  },
  // 错误处理
  proxyErrorHandler: (err, res, next) => {
    // 客户端断开连接的正常情况
    if (err.code === 'ECONNRESET' || err.code === 'EPIPE') {
      console.log('Client disconnected:', err.code);
      if (!res.headersSent) {
        res.end();
      }
      return;
    }
    
    // 超时错误处理
    if (err.code === 'ETIMEDOUT') {
      console.log('Proxy request timed out:', err.code);
      if (!res.headersSent) {
        res.status(504).send('Gateway Timeout');
      }
      return;
    }
    
    // 其他错误
    console.error('Proxy error:', err);
    if (!res.headersSent) {
      res.status(500).send('Internal Server Error');
    }
  }
});

// 配置API代理路由
app.use('/api', (req, res, next) => {
  // 检测是否为SSE请求
  const isSSE = req.headers.accept && req.headers.accept.includes('text/event-stream');
  
  if (isSSE) {
    // 使用专门的SSE代理中间件
    sseProxyMiddleware(req, res, next);
  } else {
    // 使用普通API代理中间件
    apiProxyMiddleware(req, res, next);
  }
});

// 配置代理中间件将CookieCloud请求转发给后端API
app.use(
  '/cookiecloud',
  proxy(`${proxyConfig.URL}:${proxyConfig.PORT}`, {
    // 路径加上 /cookiecloud 前缀
    proxyReqPathResolver: (req) => {
      return `/cookiecloud${req.url}`
    }
  })
);

// 处理根路径的请求
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'))
})

// 处理所有其他请求，重定向到前端入口文件
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'))
})

app.listen(port, () => {
  console.log(`Server is running on port ${port}`)
})
