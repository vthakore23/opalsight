class PerformanceAPI {
  constructor() {
    this.baseURL = 'http://localhost:8000/api/performance';
  }

  async getStatus() {
    try {
      const response = await fetch(`${this.baseURL}/status`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching performance status:', error);
      throw error;
    }
  }

  async runDatabaseTest() {
    try {
      const response = await fetch(`${this.baseURL}/test/database`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      console.error('Error running database test:', error);
      throw error;
    }
  }

  async runAPITest() {
    try {
      const response = await fetch(`${this.baseURL}/test/api`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      console.error('Error running API test:', error);
      throw error;
    }
  }

  async runSentimentTest() {
    try {
      const response = await fetch(`${this.baseURL}/test/sentiment`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      console.error('Error running sentiment test:', error);
      throw error;
    }
  }

  async runCacheTest() {
    try {
      const response = await fetch(`${this.baseURL}/test/cache`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      console.error('Error running cache test:', error);
      throw error;
    }
  }

  async runConcurrentTest(requests = 10) {
    try {
      const response = await fetch(`${this.baseURL}/test/concurrent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ requests }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error running concurrent test:', error);
      throw error;
    }
  }

  async runStressTest(duration = 30, requestsPerSecond = 10) {
    try {
      const response = await fetch(`${this.baseURL}/test/stress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ duration, requests_per_second: requestsPerSecond }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error running stress test:', error);
      throw error;
    }
  }

  async getBenchmarks() {
    try {
      const response = await fetch(`${this.baseURL}/benchmarks`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching benchmarks:', error);
      throw error;
    }
  }

  async getSystemMetrics() {
    try {
      const response = await fetch(`${this.baseURL}/metrics`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching system metrics:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const performanceAPI = new PerformanceAPI();
export default performanceAPI;
