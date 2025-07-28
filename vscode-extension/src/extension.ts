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
        const response = await client.generateCode(task);
        
        // Create content with all available data
        let content = response.code || '';
        if (response.steps && response.steps.length > 0) {
            content += '\n\n## Learning Steps:\n';
            response.steps.forEach((step: string, index: number) => {
                content += `${index + 1}. ${step}\n`;
            });
        }
        if (response.messages && response.messages.length > 0) {
            content += '\n\n## Messages:\n';
            response.messages.forEach((message: string) => {
                content += `- ${message}\n`;
            });
        }
        
        // Create a new file in the workspace
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const fileName = `generated-code-${timestamp}.md`;
        
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            const filePath = path.join(workspaceFolder.uri.fsPath, fileName);
            fs.writeFileSync(filePath, content);
            
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document);
        } else {
            // Fallback to opening in new untitled document
            const document = await vscode.workspace.openTextDocument({
                content: content,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(document);
        }
        
        vscode.window.showInformationMessage("Code generated successfully!");
    } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error occurred";
        vscode.window.showErrorMessage(`Error: ${errorMessage}`);
    }
}
      }
    )
  );
}

export function deactivate() {}
