using System;
using System.IO;
using System.Diagnostics;
using System.Text.RegularExpressions;
using System.Collections.Generic;

namespace AntigravityLauncher
{
    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string exePath = Path.Combine(appData, @"Programs\antigravity\Antigravity.exe");
            
            if (!File.Exists(exePath))
            {
                string progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
                exePath = Path.Combine(progFiles, @"Antigravity\Antigravity.exe");
            }

            if (!File.Exists(exePath))
            {
                return;
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = exePath;
            psi.WorkingDirectory = Path.GetDirectoryName(exePath);
            psi.UseShellExecute = false;

            // 检查全局代理配置
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string cfgFile = Path.Combine(userProfile, @".gemini\antigravity_proxy.json");
            
            int port = 10808;
            bool enabled = true;

            if (File.Exists(cfgFile))
            {
                try
                {
                    string json = File.ReadAllText(cfgFile);
                    if (json.Contains("\"enabled\": false") || json.Contains("\"enabled\":false"))
                    {
                        enabled = false;
                    }
                    Match m = Regex.Match(json, @"""port""\s*:\s*(\d+)");
                    if (m.Success)
                    {
                        port = int.Parse(m.Groups[1].Value);
                    }
                }
                catch {}
            }

            // 无论如何绝对不能传 --proxy-server 参数给 Antigravity.exe（会导致 Chromium 本地回环 127.0.0.1 访问被代理阻断）
            List<string> cleanArgs = new List<string>();
            if (args != null && args.Length > 0)
            {
                foreach (string arg in args)
                {
                    if (arg.IndexOf("--proxy-server", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        continue;
                    }
                    cleanArgs.Add(arg);
                }
            }

            if (enabled)
            {
                string pUrl = "http://127.0.0.1:" + port;
                string sUrl = "socks5://127.0.0.1:" + port;
                
                // 仅注入进程环境变量，供 Node.js 和后台 language_server.exe 使用
                psi.EnvironmentVariables["HTTP_PROXY"] = pUrl;
                psi.EnvironmentVariables["HTTPS_PROXY"] = pUrl;
                psi.EnvironmentVariables["ALL_PROXY"] = sUrl;
                psi.EnvironmentVariables["http_proxy"] = pUrl;
                psi.EnvironmentVariables["https_proxy"] = pUrl;
                psi.EnvironmentVariables["all_proxy"] = sUrl;
                psi.EnvironmentVariables["GRPC_PROXY"] = pUrl;
                psi.EnvironmentVariables["grpc_proxy"] = pUrl;
                psi.EnvironmentVariables["NO_PROXY"] = "localhost,127.0.0.1,::1,*.local";
                psi.EnvironmentVariables["no_proxy"] = "localhost,127.0.0.1,::1,*.local";
            }

            if (cleanArgs.Count > 0)
            {
                psi.Arguments = string.Join(" ", cleanArgs.ToArray());
            }

            try
            {
                Process.Start(psi);
            }
            catch {}
        }
    }
}