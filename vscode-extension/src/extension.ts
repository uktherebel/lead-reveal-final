import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { xAICodeGeneratorClient } from "./webSocketClient";

export async function activate(context: vscode.ExtensionContext) {
  console.log("xAI Code Generator activated!");

  const client = new xAICodeGeneratorClient();

  try {
    await client.connect();
    vscode.window.showInformationMessage("Connected to AI Tutor");
  } catch (err) {
    vscode.window.showErrorMessage("Failed to connect to backend");
  }

  // An ExtensionContext is an object provided by VS Code containing utilities and information about the extension's runtime environment

  context.subscriptions.push(
    vscode.commands.registerCommand(
      // this is 'method chaining'
      "xai-code-generator.generateCode",
      async () => {
        const task = await vscode.window.showInputBox({
          prompt: "What would you like to learn today?",
        });

        if (task) {
          try {
            const code = await client.generateCode(task);
            const editor = vscode.window.activeTextEditor;
            if (editor && !editor.document.isUntitled) {
              const success = await editor.edit((editBuilder) => {
                editBuilder.insert(editor.selection.active, code);
              });
              if (!success) {
                vscode.window.showErrorMessage("Failed to generate code");
              }
            }
          } catch (err) {
            const errorMessage =
              err instanceof Error ? err.message : "Unknown error occurred";
            vscode.window.showErrorMessage(`Error: ${errorMessage}`);
          }
        }
      }
    )
  );
}

export function deactivate() {}
