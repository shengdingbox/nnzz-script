package main

import (
	"fmt"
	"os"
	"runtime"
)

func main() {
	fmt.Println("=== 诊断信息 ===")
	fmt.Printf("操作系统: %s\n", runtime.GOOS)
	fmt.Printf("架构: %s\n", runtime.GOARCH)
	fmt.Printf("Go 版本: %s\n", runtime.Version())
	dir, _ := os.Getwd()
	fmt.Printf("当前目录: %s\n", dir)
	fmt.Printf("命令行参数: %v\n", os.Args)
	fmt.Println("=== 诊断完成 ===")
	fmt.Println("按回车键退出...")
	var input string
	fmt.Scanln(&input)
}
