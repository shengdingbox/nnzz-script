package main

import (
	"fmt"
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/widget"
)

func main() {
	fmt.Println("开始执行 Fyne 测试程序...")

	// 创建应用
	myApp := app.New()
	if myApp == nil {
		fmt.Println("创建应用失败")
		return
	}
	fmt.Println("创建应用成功")

	// 创建窗口
	myWindow := myApp.NewWindow("最小 Fyne 应用")
	if myWindow == nil {
		fmt.Println("创建窗口失败")
		return
	}
	fmt.Println("创建窗口成功")

	// 设置内容
	myWindow.SetContent(widget.NewLabel("Hello Fyne!"))
	fmt.Println("设置内容成功")

	// 显示窗口
	myWindow.Show()
	fmt.Println("显示窗口成功")

	// 运行应用
	fmt.Println("运行应用...")
	myApp.Run()

	fmt.Println("程序结束")
}
