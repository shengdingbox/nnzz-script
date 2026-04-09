package main

import (
	"embed"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

//go:embed onemain.exe
var embeddedFiles embed.FS

func main() {
	data, err := embeddedFiles.ReadFile("onemain.exe")
	if err != nil {
		fmt.Printf("读取嵌入文件失败: %v\n", err)
		return
	}

	tempDir := os.TempDir()
	tempExePath := filepath.Join(tempDir, "onemain.exe")

	if err := os.WriteFile(tempExePath, data, 0755); err != nil {
		fmt.Printf("写入临时文件失败: %v\n", err)
		return
	}
	defer os.Remove(tempExePath)

	cmd := exec.Command(tempExePath)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	fmt.Printf("正在启动: %s\n", tempExePath)

	if err := cmd.Start(); err != nil {
		fmt.Printf("启动失败: %v\n", err)
		return
	}

	fmt.Println("程序已启动")
}
